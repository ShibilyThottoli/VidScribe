"""Main video processing pipeline"""

import logging
from pathlib import Path
from typing import Dict, Optional
import time

from core.keyframe_extractor import KeyframeExtractor
from core.audio_processor import AudioProcessor
from core.groq_whisper import GroqWhisperProcessor
from generators import PPTGenerator, PDFGenerator
from utils import VideoValidator, FileHandler, create_progress_message
import config

logger = logging.getLogger(__name__)


class VideoPipeline:
    """Main pipeline for video processing"""

    def __init__(self, progress_callback=None):
        """Initialize pipeline with all components
        
        Args:
            progress_callback: Optional callable(progress: int, message: str) for progress updates
        """
        logger.info("=" * 70)
        logger.info("🚀 INITIALIZING VIDEO PROCESSING PIPELINE")
        logger.info("=" * 70)

        # Store progress callback
        self.progress_callback = progress_callback

        # Initialize components
        self.validator = VideoValidator()
        self.keyframe_extractor = KeyframeExtractor(
            motion_threshold=config.MOTION_THRESHOLD,
            histogram_threshold=config.HISTOGRAM_THRESHOLD,
            min_frame_interval=config.MIN_FRAME_INTERVAL,
            max_keyframes=config.MAX_KEYFRAMES,
        )

        # Audio extraction
        self.audio_extractor = AudioProcessor(
            output_format="ogg",  # Smallest size
            bitrate="32k",         # Good for speech
            channels=1             # Mono for speech
        )

        # Transcription using Groq Whisper API
        if config.USE_GROQ_WHISPER:
            self.transcriber = GroqWhisperProcessor(api_key=config.GROQ_API_KEY)
            logger.info("🚀 Using Groq Whisper API (cloud, fast!)")
        else:
            logger.warning("⚠️  Groq Whisper disabled - transcription will fail!")
            logger.warning("   Set USE_GROQ_WHISPER=True and provide GROQ_API_KEY")
            self.transcriber = None

        # AI processing with Gemini (dual-pool with key rotation)
        from core.gemini_processor import GeminiProcessor
        self.ai_processor = GeminiProcessor(
            api_keys=config.GEMINI_API_KEYS,  # Use list of keys for rotation
            model_name=config.GEMINI_MODEL
        )

        logger.info("✅ All pipeline components initialized")
        logger.info("=" * 70 + "\n")

    def process_video(
        self,
        video_path: str,
        output_format: str = "ppt",
        ppt_template: str = None,
        output_name: str = None,
        slide_count: int = None,
    ) -> Dict:
        """
        Process video through complete pipeline

        Args:
            video_path: Path to input video file
            output_format: Output format ('ppt', 'pdf', or 'summary')
            ppt_template: Template name for PPT (only used if format is 'ppt')
            output_name: Base name for output files (auto-generated if None)
            slide_count: Number of slides to generate (overrides config default)

        Returns:
            Dictionary with results and file paths
        """
        start_time = time.time()

        logger.info("\n" + "=" * 70)
        logger.info(f"🎬 PROCESSING VIDEO: {Path(video_path).name}")
        logger.info(f"📊 Output Format: {output_format.upper()}")
        if output_format == "ppt":
            logger.info(f"🎨 Template: {ppt_template or config.DEFAULT_TEMPLATE}")
        logger.info("=" * 70)

        results = {
            "status": "processing",
            "video_path": video_path,
            "output_format": output_format,
            "start_time": start_time,
        }

        try:
            # Step 1: Validate video
            logger.info(f"\n{create_progress_message(1, 6, 'Validating video')}")
            is_valid, error = self.validator.validate_file(video_path)
            if not is_valid:
                raise ValueError(f"Video validation failed: {error}")

            video_info = self.validator.get_video_info(video_path)
            results["video_info"] = video_info
            logger.info(
                f"✅ Video valid: {video_info['duration_formatted']}, {video_info['resolution']}"
            )
            self._update_progress(16, 'Video validated')

            # Generate output name
            if output_name is None:
                output_name = Path(video_path).stem

            # Create temp directory
            temp_dir = config.TEMP_FOLDER / output_name
            temp_dir.mkdir(parents=True, exist_ok=True)

            # Determine if we need visual processing (keyframes + captions)
            needs_visuals = output_format in ['ppt', 'pdf']
            
            # Step 2: Extract keyframes (SKIP for summary-only)
            if needs_visuals:
                logger.info(
                    f"\n{create_progress_message(2, 6, 'Extracting keyframes with OpenCV')}"
                )
                
                keyframes_dir = temp_dir / "keyframes"
                
                # Calculate max keyframes based on slide count
                # 10 slides → 4 keyframes, 15 slides → 7 keyframes, 20 slides → 12 keyframes
                num_slides = slide_count if slide_count is not None else config.PPT_SLIDES_COUNT
                if num_slides <= 10:
                    max_keyframes = 4
                elif num_slides <= 15:
                    max_keyframes = 7
                else:  # 20+ slides
                    max_keyframes = 12
                
                logger.info(f"📊 Slide count: {num_slides} → Max keyframes: {max_keyframes}")
                
                # Temporarily override max_keyframes for this extraction
                original_max = self.keyframe_extractor.max_keyframes
                self.keyframe_extractor.max_keyframes = max_keyframes
                
                keyframes = self.keyframe_extractor.extract_keyframes(
                    video_path, str(keyframes_dir)
                )
                
                # Restore original max_keyframes
                self.keyframe_extractor.max_keyframes = original_max
                
                keyframe_paths = [kf[1] for kf in keyframes]
                results["keyframe_count"] = len(keyframes)
                logger.info(f"✅ Extracted {len(keyframes)} keyframes")
                self._update_progress(33, f'Extracted {len(keyframes)} keyframes')
            else:
                # Skip keyframe extraction for summary
                logger.info(
                    f"\n{create_progress_message(2, 6, 'Skipping keyframes (summary mode)')}"
                )
                logger.info("⏩ Keyframe extraction skipped - not needed for text summary")
                keyframe_paths = []
                results["keyframe_count"] = 0
                self._update_progress(33, 'Skipped keyframe extraction')

            # Step 3: Extract audio and transcribe
            logger.info(
                f"\n{create_progress_message(3, 6, 'Extracting & transcribing audio')}"
            )
            audio_path = temp_dir / "audio.ogg"

            # Extract audio to OGG (compressed)
            audio_path_str = self.audio_extractor.extract_audio(video_path, str(audio_path))

            # Transcribe using Groq Whisper
            if config.USE_GROQ_WHISPER and self.transcriber:
                transcript_data = self.transcriber.transcribe_audio(
                    audio_path_str, 
                    language=config.WHISPER_LANGUAGE
                )
            else:
                raise ValueError("Groq Whisper is not configured. Set USE_GROQ_WHISPER=True and provide GROQ_API_KEY")

            results["transcript"] = transcript_data["text"]
            results["language"] = transcript_data.get("language", "unknown")
            logger.info(
                f"✅ Transcription complete: {len(transcript_data['text'])} characters"
            )
            self._update_progress(50, 'Audio transcribed')

            # Step 4: Generate captions (SKIP for summary-only)
            if needs_visuals:
                logger.info(f"\n{create_progress_message(4, 6, 'Generating captions with Gemini AI')}")
                
                captions = self.ai_processor.generate_captions_batch(
                    keyframe_paths, delay=0.5
                )
                logger.info(f"✅ Generated {len(captions)} captions")
                results["captions"] = captions
                self._update_progress(66, 'Image captions generated')
            else:
                # Skip caption generation for summary
                logger.info(f"\n{create_progress_message(4, 6, 'Skipping captions (summary mode)')}")
                logger.info("⏩ Caption generation skipped - not needed for text summary")
                results["captions"] = []
                self._update_progress(66, 'Skipped caption generation')
            
            # Step 5: Create summary
            logger.info(f"\n{create_progress_message(5, 6, 'Creating structured summary')}")
            
            # Use custom slide count or fall back to config default
            num_slides = slide_count if slide_count is not None else config.PPT_SLIDES_COUNT
            logger.info(f"📊 Generating {num_slides} content slides")
            
            summary_data = self.ai_processor.create_content_sections(
                transcript_data["text"], num_sections=num_slides
            )
            logger.info(f"✅ Summary created: '{summary_data['title']}'")

            self._update_progress(83, 'Content summarized')

            # Set common results
            results["title"] = summary_data["title"]
            results["overview"] = summary_data["overview"]
            
            # Build comprehensive summary for summary-only format
            if output_format == "summary":
                # Create detailed text summary with all sections
                summary_parts = []
                
                # Add title
                summary_parts.append(f"# {summary_data['title']}\n")
                
                # Add overview
                summary_parts.append(f"## Overview\n{summary_data['overview']}\n")
                
                # Add all sections with content
                for i, section in enumerate(summary_data["sections"], 1):
                    summary_parts.append(f"## {i}. {section['title']}")
                    summary_parts.append("\n".join(f"• {point}" for point in section["content"]))
                    summary_parts.append("")  # Empty line between sections
                
                # Add key takeaways
                if summary_data.get("takeaways"):
                    summary_parts.append("## Key Takeaways")
                    summary_parts.append("\n".join(f"✓ {point}" for point in summary_data["takeaways"]))
                
                # Join all parts with newlines
                results["summary"] = "\n\n".join(summary_parts)
                logger.info(f"📝 Built comprehensive summary: {len(results['summary'])} characters")
            else:
                # For PPT/PDF, just use the overview
                results["summary"] = summary_data["overview"]
            
            # Create slides data (only if needed for PPT/PDF)
            if needs_visuals:
                slides = []
                for i, section in enumerate(summary_data["sections"]):
                    # Match keyframes to sections
                    keyframe_path = None
                    if i < len(keyframe_paths):
                        keyframe_path = keyframe_paths[i]

                    slides.append(
                        {
                            "number": i + 1,
                            "title": section["title"],
                            "content": "\n".join(section["content"]),
                            "keyframe_path": keyframe_path,
                        }
                    )

                # Add takeaways slide
                if summary_data.get("takeaways"):
                    slides.append(
                        {
                            "number": len(slides) + 1,
                            "title": "Key Takeaways",
                            "content": "\n".join(summary_data["takeaways"]),
                        }
                    )

                results["slides"] = slides
            else:
                # For summary mode, we don't need slides data
                results["slides"] = []
                logger.info("⏩ Slide creation skipped - returning text summary only")

            # Step 6: Generate output
            logger.info(
                f"\n{create_progress_message(6, 6, f'Generating {output_format.upper()} output')}"
            )

            if output_format == "ppt":
                output_path = self._generate_ppt(
                    slides, output_name, summary_data, ppt_template
                )
                results["output_path"] = output_path
                results["output_type"] = "ppt"
                results["template"] = ppt_template or config.DEFAULT_TEMPLATE

            elif output_format == "pdf":
                output_path = self._generate_pdf(slides, output_name, summary_data)
                results["output_path"] = output_path
                results["output_type"] = "pdf"

            elif output_format == "summary":
                # Summary only - no file generation
                results["output_type"] = "summary"
                results["output_path"] = None
                logger.info("✅ Summary ready for display")

            else:
                raise ValueError(f"Invalid output format: {output_format}")

            self._update_progress(100, 'Output generated successfully')

            # Cleanup
            if config.AUTO_DELETE_TEMP:
                FileHandler.cleanup_temp_files(output_name)

            if config.AUTO_DELETE_UPLOADS:
                FileHandler.cleanup_upload(video_path)

            # Calculate processing time
            processing_time = time.time() - start_time
            results["processing_time"] = processing_time
            results["status"] = "complete"

            logger.info("\n" + "=" * 70)
            logger.info(f"✅ PROCESSING COMPLETE!")
            logger.info(f"⏱️  Total time: {processing_time:.2f} seconds")
            logger.info("=" * 70 + "\n")

            return results

        except Exception as e:
            logger.error(f"❌ Pipeline error: {e}", exc_info=True)
            results["status"] = "error"
            results["error"] = str(e)
            return results

    def _update_progress(self, progress: int, message: str):
        """Update progress via callback if available"""
        if self.progress_callback:
            try:
                self.progress_callback(progress, message)
            except Exception as e:
                logger.warning(f"Progress callback error: {e}")

    def _generate_ppt(
        self, slides: list, output_name: str, summary_data: dict, template: str = None
    ) -> str:
        """Generate PowerPoint presentation"""

        generator = PPTGenerator(template_name=template)
        output_path = config.OUTPUT_FOLDER / f"{output_name}.pptx"

        generator.create_presentation(
            slides,
            str(output_path),
            title=summary_data["title"],
            subtitle=summary_data["overview"],
        )

        logger.info(f"✅ PowerPoint created: {output_path}")
        return str(output_path)

    def _generate_pdf(self, slides: list, output_name: str, summary_data: dict) -> str:
        """Generate PDF report"""

        generator = PDFGenerator()
        output_path = config.OUTPUT_FOLDER / f"{output_name}.pdf"

        generator.generate_pdf(
            slides_data=slides,
            output_path=str(output_path),
            title=summary_data["title"],
            summary=summary_data["overview"],
        )

        logger.info(f"✅ PDF created: {output_path}")
        return str(output_path)


def main():
    """CLI entry point for testing"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python video_pipeline.py <video_path> [output_format] [template]")
        print("  output_format: ppt (default), pdf, or summary")
        print(
            "  template: professional (default), educational, minimalist, creative, modern_tech"
        )
        sys.exit(1)

    video_path = sys.argv[1]
    output_format = sys.argv[2] if len(sys.argv) > 2 else "ppt"
    template = sys.argv[3] if len(sys.argv) > 3 else None

    # Setup logging
    from utils import setup_logger

    setup_logger()

    # Run pipeline
    pipeline = VideoPipeline()
    results = pipeline.process_video(
        video_path, output_format=output_format, ppt_template=template
    )

    if results["status"] == "complete":
        print("\n✅ Video processing complete!")
        print(f"  - Title: {results['title']}")
        print(f"  - Slides: {len(results['slides'])}")
        print(f"  - Language: {results['language']}")
        print(f"  - Processing time: {results['processing_time']:.2f}s")
        if results.get("output_path"):
            print(f"  - Output: {results['output_path']}")
    else:
        print(f"\n❌ Error: {results.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()