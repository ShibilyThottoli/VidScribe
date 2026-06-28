"""YouTube video downloader utility"""

import logging
from pathlib import Path
from typing import Tuple, Optional
import yt_dlp
import re

logger = logging.getLogger(__name__)


class YouTubeDownloader:
    """Handle YouTube video downloads"""
    
    def __init__(self, output_dir: str = "uploads"):
        """
        Initialize YouTube downloader
        
        Args:
            output_dir: Directory to save downloaded videos
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def is_valid_youtube_url(url: str) -> bool:
        """
        Check if URL is a valid YouTube URL
        
        Args:
            url: URL string to validate
            
        Returns:
            True if valid YouTube URL, False otherwise
        """
        youtube_patterns = [
            r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+',
            r'(https?://)?(www\.)?youtube\.com/watch\?v=[\w-]+',
            r'(https?://)?(www\.)?youtu\.be/[\w-]+',
            r'(https?://)?(www\.)?youtube\.com/embed/[\w-]+',
            r'(https?://)?(www\.)?youtube\.com/v/[\w-]+',
        ]
        
        return any(re.match(pattern, url) for pattern in youtube_patterns)
    
    def get_video_info(self, url: str) -> Optional[dict]:
        """
        Get video information without downloading
        
        Args:
            url: YouTube video URL
            
        Returns:
            Dictionary with video info or None if error
        """
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                return {
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'duration_formatted': self._format_duration(info.get('duration', 0)),
                    'uploader': info.get('uploader', 'Unknown'),
                    'view_count': info.get('view_count', 0),
                    'upload_date': info.get('upload_date', 'Unknown'),
                    'thumbnail': info.get('thumbnail', ''),
                }
        
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            return None
    
    def download_video(self, url: str, output_filename: str = None) -> Tuple[bool, str]:
        """
        Download YouTube video
        
        Args:
            url: YouTube video URL
            output_filename: Custom filename (without extension)
            
        Returns:
            Tuple of (success: bool, file_path or error_message: str)
        """
        try:
            logger.info(f"Starting YouTube download: {url}")
            
            # Validate URL
            if not self.is_valid_youtube_url(url):
                return False, "Invalid YouTube URL"
            
            # Generate output template
            if output_filename:
                # Use custom filename
                output_template = str(self.output_dir / f"{output_filename}.%(ext)s")
                expected_file = self.output_dir / f"{output_filename}.mp4"
            else:
                # Use video ID only for simpler, more reliable filenames
                output_template = str(self.output_dir / "%(id)s.%(ext)s")
                expected_file = None  # We'll determine this after getting video info
            
            # Download options - UPDATED for better audio+video merging
            ydl_opts = {
                # Format: best video + best audio, merge to mp4
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': output_template,
                'quiet': False,
                'no_warnings': False,
                'merge_output_format': 'mp4',
                # Force merge even if video has audio
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }],
                # Prefer formats with audio
                'prefer_free_formats': True,
                # Don't use HLS/DASH if possible (causes issues)
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android', 'web']
                    }
                },
            }
            
            # Download video
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.info("Extracting video information...")
                info = ydl.extract_info(url, download=True)
                
                if not info:
                    return False, "Failed to extract video information"
                
                video_id = info.get('id', 'unknown')
                
                # Determine downloaded file path
                if output_filename:
                    downloaded_file = expected_file
                else:
                    # File was saved as video_id.mp4
                    downloaded_file = self.output_dir / f"{video_id}.mp4"
                
                # Verify file exists and is not empty
                if not downloaded_file.exists():
                    # Try to find any .mp4 file with the video ID
                    possible_files = list(self.output_dir.glob(f"*{video_id}*.mp4"))
                    if possible_files:
                        downloaded_file = possible_files[0]
                        logger.info(f"Found downloaded file: {downloaded_file}")
                    else:
                        return False, f"Downloaded file not found. Expected: {downloaded_file}"
                
                # Check if file is not empty
                file_size = downloaded_file.stat().st_size
                if file_size == 0:
                    logger.error("Downloaded file is empty (0 bytes)")
                    downloaded_file.unlink()  # Delete empty file
                    return False, "Downloaded file is empty. YouTube may have blocked the download."
                
                logger.info(f"✅ Download complete: {downloaded_file}")
                logger.info(f"   Size: {file_size / (1024*1024):.2f}MB")
                
                # Check for audio using ffprobe or moviepy
                has_audio = self._check_audio_track(str(downloaded_file))
                if not has_audio:
                    logger.warning("⚠️  Downloaded video may not have audio track!")
                    logger.warning("   This could cause issues during transcription.")
                
                return True, str(downloaded_file)
        
        except Exception as e:
            error_msg = f"Download error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg
    
    def _check_audio_track(self, video_path: str) -> bool:
        """
        Check if video has an audio track using MoviePy
        
        Args:
            video_path: Path to video file
            
        Returns:
            True if audio track detected, False otherwise
        """
        try:
            from moviepy import VideoFileClip
            video = VideoFileClip(video_path)
            has_audio = video.audio is not None
            video.close()
            return has_audio
        except Exception as e:
            logger.warning(f"Could not check audio track: {e}")
            return True  # Assume it has audio if we can't check
    
    @staticmethod
    def _format_duration(seconds: int) -> str:
        """Format duration in seconds to HH:MM:SS"""
        if not seconds:
            return "Unknown"
        
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
    
    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """Remove invalid characters from filename and make URL-safe"""
        import re
        
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*#%&{}[]@!$\'^+=`~;,'
        for char in invalid_chars:
            filename = filename.replace(char, '')
        
        # Replace spaces and multiple underscores with single underscore
        filename = re.sub(r'[\s_]+', '_', filename)
        
        # Remove leading/trailing underscores
        filename = filename.strip('_')
        
        # Limit length
        return filename[:80]


# Test function
def main():
    """Test YouTube downloader"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python youtube_downloader.py <youtube_url>")
        sys.exit(1)
    
    url = sys.argv[1]
    
    downloader = YouTubeDownloader()
    
    # Get info
    print("📺 Getting video info...")
    info = downloader.get_video_info(url)
    
    if info:
        print(f"✅ Title: {info['title']}")
        print(f"✅ Duration: {info['duration_formatted']}")
        print(f"✅ Uploader: {info['uploader']}")
    
    # Download
    print("\n📥 Downloading video...")
    success, result = downloader.download_video(url)
    
    if success:
        print(f"✅ Success! File saved to: {result}")
    else:
        print(f"❌ Error: {result}")


if __name__ == "__main__":
    main()
