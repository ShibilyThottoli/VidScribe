"""Flask application for video summarization"""

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from werkzeug.utils import secure_filename
import os
import logging
from pathlib import Path
import threading

from pipeline import VideoPipeline
from utils import VideoValidator, FileHandler, get_unique_filename, setup_logger
from generators import get_available_templates
import config

# Setup logging
setup_logger()
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = config.MAX_FILE_SIZE
app.config['SECRET_KEY'] = config.FLASK_SECRET_KEY

# Initialize components
validator = VideoValidator()
file_handler = FileHandler()

# Store processing results (in-memory, use Redis in production)
processing_status = {}
processing_results = {}


@app.route('/')
def index():
    """Main page"""
    templates = get_available_templates()
    return render_template('index.html', templates=templates, config=config)


@app.route('/upload', methods=['POST'])
def upload_video():
    """Handle video upload or YouTube URL"""
    
    logger.info("Upload request received")
    
    # Check for YouTube URL first
    youtube_url = request.form.get('youtube_url', '').strip()
    
    # Get form parameters
    output_format = request.form.get('output_format', 'ppt')
    template = request.form.get('ppt_template', config.DEFAULT_TEMPLATE)
    slide_count = request.form.get('slide_count', '10')  # Default: 10 slides (Short)
    
    filepath = None
    video_info = None
    output_name = None
    
    try:
        # Handle YouTube URL
        if youtube_url:
            from utils.youtube_downloader import YouTubeDownloader
            
            logger.info(f"YouTube URL provided: {youtube_url}")
            
            # Validate YouTube URL
            if not YouTubeDownloader.is_valid_youtube_url(youtube_url):
                return jsonify({'error': 'Invalid YouTube URL. Please provide a valid YouTube video link.'}), 400
            
            # Download video
            downloader = YouTubeDownloader(config.UPLOAD_FOLDER)
            
            try:
                success, result = downloader.download_video(youtube_url)
                
                if not success:
                    logger.error(f"YouTube download failed: {result}")
                    return jsonify({'error': f'Failed to download YouTube video: {result}'}), 400
                
                filepath = result
                logger.info(f"YouTube video downloaded: {filepath}")
                
                # Get video info
                video_info = validator.get_video_info(filepath)
                
                # Generate processing ID from downloaded filename
                output_name = Path(filepath).stem
                
            except Exception as download_error:
                logger.error(f"YouTube download error: {download_error}")
                return jsonify({'error': f'Failed to download YouTube video: {str(download_error)}'}), 400
        
        # Handle file upload
        else:
            # Check if file exists
            if 'video' not in request.files:
                return jsonify({'error': config.ERROR_MESSAGES['no_file']}), 400
            
            file = request.files['video']
            
            if file.filename == '':
                return jsonify({'error': config.ERROR_MESSAGES['no_file']}), 400
            
            logger.info(f"File upload: {file.filename}")
            
            # Save uploaded file
            filename = secure_filename(file.filename)
            unique_filename = get_unique_filename(filename)
            filepath = file_handler.save_upload(file, unique_filename)
            
            logger.info(f"File saved: {filepath}")
            
            # Validate video
            is_valid, error = validator.validate_file(filepath)
            if not is_valid:
                file_handler.delete_file(filepath)
                return jsonify({'error': error}), 400
            
            # Get video info
            video_info = validator.get_video_info(filepath)
            
            # Generate processing ID
            output_name = Path(unique_filename).stem
        
        logger.info(f"Upload details: format={output_format}, template={template}, output_name={output_name}")
        
        # Initialize processing status
        processing_status[output_name] = {
            'status': 'queued',
            'progress': 0,
            'message': 'Video uploaded successfully' if not youtube_url else 'YouTube video downloaded successfully'
        }
        
        # Start processing in background thread
        thread = threading.Thread(
            target=process_video_background,
            args=(filepath, output_format, template, output_name, slide_count)
        )
        thread.daemon = True
        thread.start()
        
        logger.info(f"Processing started for: {output_name}")
        
        return jsonify({
            'status': 'success',
            'output_name': output_name,
            'video_info': {
                'duration': video_info['duration_formatted'],
                'resolution': video_info['resolution'],
                'size': f"{video_info['file_size_mb']:.2f} MB"
            },
            'message': 'Video uploaded and processing started' if not youtube_url else 'YouTube video downloaded and processing started'
        })
        
    except Exception as e:
        logger.error(f"Upload error: {e}", exc_info=True)
        if filepath and Path(filepath).exists():
            try:
                file_handler.delete_file(filepath)
            except Exception:
                pass
        return jsonify({'error': str(e)}), 500


def process_video_background(video_path: str, output_format: str, 
                            template: str, output_name: str, slide_count: str = '10'):
    """Process video in background thread"""
    
    try:
        # Define progress callback to update status
        def update_progress(progress: int, message: str):
            processing_status[output_name] = {
                'status': 'processing',
                'progress': progress,
                'message': message
            }
            logger.info(f"Progress: {progress}% - {message}")
        
        # Initialize pipeline with progress callback
        pipeline = VideoPipeline(progress_callback=update_progress)
        
        # Process video with custom slide count
        results = pipeline.process_video(
            video_path=video_path,
            output_format=output_format,
            ppt_template=template if output_format == 'ppt' else None,
            output_name=output_name,
            slide_count=int(slide_count) if output_format == 'ppt' else None
        )
        
        # Store results
        processing_results[output_name] = results
        
        if results['status'] == 'complete':
            # Auto-save results to JSON for reuse
            try:
                import json
                import shutil
                
                saved_dir = Path(__file__).parent / "saved_results"
                saved_dir.mkdir(exist_ok=True)
                saved_path = saved_dir / f"{output_name}.json"
                
                # Save JSON data
                with open(saved_path, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)
                
                # Save keyframe images
                keyframes_saved_dir = saved_dir / f"{output_name}_keyframes"
                keyframes_saved_dir.mkdir(exist_ok=True)
                
                if results.get('slides'):
                    saved_count = 0
                    for slide in results['slides']:
                        if slide.get('keyframe_path'):
                            src_path = Path(slide['keyframe_path'])
                            if src_path.exists():
                                dst_path = keyframes_saved_dir / src_path.name
                                shutil.copy2(src_path, dst_path)
                                # Update path in results to point to saved location
                                slide['keyframe_path'] = str(dst_path)
                                saved_count += 1
                    
                    # Re-save JSON with updated keyframe paths
                    with open(saved_path, 'w', encoding='utf-8') as f:
                        json.dump(results, f, indent=2, ensure_ascii=False)
                    
                    logger.info(f"💾 Auto-saved results to: {saved_path}")
                    logger.info(f"   Saved {saved_count} keyframe images")
                else:
                    logger.info(f"💾 Auto-saved results to: {saved_path}")
                
                logger.info(f"   Reuse via: http://localhost:{config.FLASK_PORT}/saved/{output_name}")
            except Exception as e:
                logger.warning(f"Failed to auto-save results: {e}")
            
            processing_status[output_name] = {
                'status': 'complete',
                'progress': 100,
                'message': 'Processing complete!'
            }
        else:
            processing_status[output_name] = {
                'status': 'error',
                'progress': 0,
                'message': results.get('error', 'Unknown error')
            }
            
    except Exception as e:
        logger.error(f"Background processing error: {e}", exc_info=True)
        processing_status[output_name] = {
            'status': 'error',
            'progress': 0,
            'message': str(e)
        }


@app.route('/status/<output_name>')
def get_status(output_name):
    """Get processing status"""
    
    if output_name not in processing_status:
        return jsonify({'error': 'Not found'}), 404
    
    status = processing_status[output_name]
    
    # Add results if complete
    if status['status'] == 'complete' and output_name in processing_results:
        results = processing_results[output_name]
        status['results'] = {
            'title': results.get('title', 'Video Summary'),
            'summary': results.get('summary', ''),
            'slides_count': len(results.get('slides', [])),
            'language': results.get('language', 'unknown'),
            'processing_time': results.get('processing_time', 0),
            'output_type': results.get('output_type'),
            'output_path': Path(results.get('output_path', '')).name if results.get('output_path') else None
        }
    
    return jsonify(status)


@app.route('/download/<output_name>')
def download_file(output_name):
    """Download generated file"""
    
    if output_name not in processing_results:
        return jsonify({'error': 'Results not found'}), 404
    
    results = processing_results[output_name]
    
    if results['status'] != 'complete':
        return jsonify({'error': 'Processing not complete'}), 400
    
    output_path = results.get('output_path')
    
    if not output_path or not os.path.exists(output_path):
        return jsonify({'error': 'File not found'}), 404
    
    # Determine mimetype and extension
    output_type = results.get('output_type', 'ppt')
    if output_type == 'ppt':
        mimetype = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
        ext = '.pptx'
    elif output_type == 'pdf':
        mimetype = 'application/pdf'
        ext = '.pdf'
    else:
        return jsonify({'error': 'Invalid output type'}), 400
    
    # Use a cleaner filename from the actual file, not the output_name
    filename = Path(output_path).name
    
    # Ensure the filename has the proper extension
    if not filename.endswith(ext):
        filename = f"{Path(filename).stem}{ext}"
    
    response = send_file(
        output_path,
        as_attachment=True,
        download_name=filename,
        mimetype=mimetype
    )
    
    # Explicitly set Content-Disposition header to ensure proper filename
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    
    return response


@app.route('/templates')
def list_templates():
    """Get available templates"""
    templates = get_available_templates()
    return jsonify({'templates': templates})


@app.route('/regenerate-ppt/<output_name>', methods=['POST'])
def regenerate_ppt(output_name):
    """Regenerate PPT with different template (no API calls, uses cached data)"""
    
    try:
        # Get requested template from request body
        data = request.get_json()
        new_template = data.get('template', config.DEFAULT_TEMPLATE)
        
        logger.info(f"🔄 Regenerating PPT for '{output_name}' with template '{new_template}'")
        
        # Check if results exist in memory or load from saved JSON
        if output_name not in processing_results:
            # Try loading from saved_results
            saved_path = Path(__file__).parent / "saved_results" / f"{output_name}.json"
            if saved_path.exists():
                import json
                with open(saved_path, 'r', encoding='utf-8') as f:
                    results = json.load(f)
                processing_results[output_name] = results
                logger.info(f"✅ Loaded cached results from {saved_path}")
            else:
                return jsonify({'error': 'Results not found'}), 404
        
        results = processing_results[output_name]
        
        # Verify results are complete
        if results['status'] != 'complete':
            return jsonify({'error': 'Processing not complete'}), 400
        
        # Import PPTGenerator
        from generators.ppt_generator import PPTGenerator
        
        # Generate new filename with template name
        timestamp = Path(results.get('output_path', '')).stem.split('_')[-1] if results.get('output_path') else 'regenerated'
        new_filename = f"{output_name}_{new_template}_{timestamp}.pptx"
        new_output_path = config.OUTPUT_FOLDER / new_filename
        
        # Create PPT with new template using cached slides data
        generator = PPTGenerator(template_name=new_template)
        generator.create_presentation(
            slides_data=results.get('slides', []),
            output_path=str(new_output_path),
            title=results.get('title', 'Video Summary'),
            subtitle=results.get('summary', '')[:120] if results.get('summary') else None
        )
        
        # Update results with new template and output path
        results['template'] = new_template
        results['output_path'] = str(new_output_path)
        
        logger.info(f"✅ Regenerated PPT: {new_output_path}")
        logger.info(f"   Template: {new_template}")
        logger.info(f"   No Gemini API calls made! 🎉")
        
        return jsonify({
            'status': 'success',
            'message': 'PPT regenerated successfully',
            'template': new_template,
            'output_path': new_filename,
            'download_url': f'/download/{output_name}'
        })
        
    except Exception as e:
        logger.error(f"Error regenerating PPT: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/results/<output_name>')
def show_results(output_name):
    """Display results page with presentation and template selection"""
    
    # Check if results exist
    if output_name not in processing_results:
        # Try loading from saved_results
        saved_path = Path(__file__).parent / "saved_results" / f"{output_name}.json"
        if saved_path.exists():
            import json
            try:
                with open(saved_path, 'r', encoding='utf-8') as f:
                    results = json.load(f)
                processing_results[output_name] = results
                processing_status[output_name] = {
                    'status': 'complete',
                    'progress': 100,
                    'message': 'Loaded from saved results'
                }
                logger.info(f"✅ Loaded saved results: {output_name}")
            except Exception as e:
                logger.error(f"Error loading saved results: {e}")
                return render_template('index.html', 
                                     templates=get_available_templates(),
                                     config=config,
                                     error='Results not found'), 404
        else:
            return render_template('index.html', 
                                 templates=get_available_templates(), 
                                 config=config,
                                 error='Results not found'), 404
    
    results = processing_results[output_name]
    
    # Check if processing is complete
    if results['status'] != 'complete':
        return render_template('index.html',
                             templates=get_available_templates(),
                             config=config,
                             error='Processing not complete'), 400
    
    # Render INDEX.HTML with results data
    return render_template('index.html',
                         templates=get_available_templates(),
                         config=config,
                         # Results data passed to index.html
                         slides=results.get('slides', []),
                         output_name=output_name,
                         selected_template=results.get('template', config.DEFAULT_TEMPLATE),
                         presentation_title=results.get('title', 'Video Summary'),
                         output_format=results.get('output_type', 'ppt'),
                         summary=results.get('summary', ''))


@app.route('/test-results')
def test_results():
    """Test endpoint with dummy data for results page preview"""
    
    # Create dummy data for testing
    test_output_name = 'test_demo'
    
    # Mock slides data
    dummy_slides = [
        {
            'number': 1,
            'title': 'Introduction to AI',
            'content': 'Artificial Intelligence is transforming the world.\nMachine learning enables computers to learn from data.\nDeep learning uses neural networks for complex tasks.',
            'keyframe_path': None
        },
        {
            'number': 2,
            'title': 'Machine Learning Basics',
            'content': 'Supervised learning uses labeled data.\nUnsupervised learning finds patterns.\nReinforcement learning learns through rewards.',
            'keyframe_path': None
        },
        {
            'number': 3,
            'title': 'Neural Networks',
            'content': 'Neurons process information in layers.\nActivation functions introduce non-linearity.\nBackpropagation trains the network.',
            'keyframe_path': None
        },
        {
            'number': 4,
            'title': 'Deep Learning Applications',
            'content': 'Computer vision for image recognition.\nNatural language processing for text.\nSpeech recognition and generation.',
            'keyframe_path': None
        },
        {
            'number': 5,
            'title': 'Future of AI',
            'content': 'AI will continue to advance rapidly.\nEthical considerations are crucial.\nHuman-AI collaboration is the future.',
            'keyframe_path': None
        },
        {
            'number': 6,
            'title': 'Conclusion',
            'content': 'AI is reshaping every industry.\nContinuous learning is essential.\nThe future is intelligent and exciting.',
            'keyframe_path': None
        }
    ]
    
    # Create dummy results
    processing_results[test_output_name] = {
        'status': 'complete',
        'title': 'AI & Machine Learning: A Complete Guide',
        'summary': 'This presentation covers the fundamentals of artificial intelligence and machine learning, including neural networks, deep learning applications, and the future of AI technology.',
        'slides': dummy_slides,
        'output_path': '/dummy/path/presentation.pptx',
        'template': 'professional',
        'output_type': 'ppt',
        'processing_time': 45.2,
        'language': 'en'
    }
    
    # Also set processing status
    processing_status[test_output_name] = {
        'status': 'complete',
        'progress': 100,
        'message': 'Processing complete!'
    }
    
    # Redirect to results page
    from flask import redirect, url_for
    return redirect(url_for('show_results', output_name=test_output_name))


@app.route('/saved/<filename>')
def show_saved_results(filename):
    """Load and display saved results from JSON file (no API usage)"""
    import json
    
    # Load saved results
    saved_path = Path(__file__).parent / "saved_results" / f"{filename}.json"
    
    logger.info(f"🔍 Attempting to load saved results: {filename}")
    logger.info(f"   Looking for file: {saved_path}")
    logger.info(f"   File exists: {saved_path.exists()}")
    
    if not saved_path.exists():
        logger.error(f"❌ File not found: {saved_path}")
        return render_template('index.html',
                             templates=get_available_templates(),
                             config=config,
                             error=f'Saved result not found: {filename}'), 404
    
    try:
        with open(saved_path, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        # Check if referenced template exists, fallback to default if not
        if 'template' in results:
            template_path = Path(__file__).parent / 'generators' / 'templates' / f"{results['template']}.pptx"
            if not template_path.exists():
                logger.warning(f"Template '{results['template']}.pptx' not found, using default: {config.DEFAULT_TEMPLATE}")
                results['template'] = config.DEFAULT_TEMPLATE
        
        # Load into memory so it can be accessed by other routes
        processing_results[filename] = results
        processing_status[filename] = {
            'status': 'complete',
            'progress': 100,
            'message': 'Loaded from saved results'
        }
        
        logger.info(f"✅ Loaded saved results: {filename}")
        logger.info(f"   - Slides: {len(results.get('slides', []))}")
        
        # Redirect to results page
        return redirect(url_for('show_results', output_name=filename))

        
    except Exception as e:
        logger.error(f"Error loading saved results: {e}")
        return render_template('index.html',
                             templates=get_available_templates(),
                             config=config,
                             error=f'Error loading results: {str(e)}'), 500



@app.route('/cleanup', methods=['POST'])
def cleanup():
    """Cleanup old files"""
    try:
        file_handler.cleanup_old_outputs(hours=config.KEEP_OUTPUTS_HOURS)
        return jsonify({'status': 'success', 'message': 'Cleanup complete'})
    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/temp/<path:filename>')
def serve_temp_file(filename):
    """Serve files from temp folder or saved_results (keyframes, etc)"""
    try:
        # First try temp folder (for currently processing videos)
        temp_path = config.TEMP_FOLDER / filename
        if temp_path.exists():
            return send_file(str(temp_path))
        
        # Then try saved_results folder (for saved keyframes)
        saved_path = Path(__file__).parent / "saved_results" / filename
        if saved_path.exists():
            return send_file(str(saved_path))
        
        return "File not found", 404
    except Exception as e:
        logger.error(f"Error serving temp file: {e}")
        return "Error serving file", 500


@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large error"""
    max_gb = config.MAX_FILE_SIZE / (1024 ** 3)
    return jsonify({'error': f'File size exceeds {max_gb:.1f}GB limit'}), 413


@app.errorhandler(500)
def internal_error(error):
    """Handle internal server error"""
    logger.error(f"Internal error: {error}")
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    # Ensure directories exist
    file_handler.ensure_directories()
    
    # Run app
    logger.info("="*70)
    logger.info("🚀 Starting VidScribe Application")
    logger.info("="*70)
    logger.info(f"Host: {config.FLASK_HOST}")
    logger.info(f"Port: {config.FLASK_PORT}")
    logger.info(f"Debug: {config.FLASK_DEBUG}")
    logger.info("="*70)
    
    app.run(
        debug=config.FLASK_DEBUG,
        host=config.FLASK_HOST,
        port=config.FLASK_PORT
    )