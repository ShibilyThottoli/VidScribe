"""Audio extraction and transcription using MoviePy and Groq Whisper"""

import os
import logging
from pathlib import Path
from pydub import AudioSegment

try:
    from moviepy import VideoFileClip
except ImportError:
    from moviepy.editor import VideoFileClip

logger = logging.getLogger(__name__)


class AudioProcessor:
    """Extract audio from video in optimal format for transcription"""
    
    def __init__(self, output_format="ogg", bitrate="32k", channels=1):
        """
        Initialize AudioProcessor
        
        Args:
            output_format: Audio format (ogg, mp3, m4a) - ogg is smallest
            bitrate: Audio bitrate (32k for speech is optimal)
            channels: Number of audio channels (1=mono for speech)
        """
        self.output_format = output_format
        self.bitrate = bitrate
        self.channels = channels
        
    def extract_audio(self, video_path: str, audio_path: str = None) -> str:
        """
        Extract audio from video file in compressed format
        
        Args:
            video_path: Path to input video
            audio_path: Path to save audio (optional, auto-generated if None)
            
        Returns:
            Path to extracted audio file
        """
        logger.info("="*60)
        logger.info("🎵 AUDIO EXTRACTION")
        logger.info(f"   Video: {Path(video_path).name}")
        logger.info(f"   Format: {self.output_format.upper()}")
        logger.info(f"   Bitrate: {self.bitrate}")
        logger.info(f"   Channels: {self.channels} (mono)")
        logger.info("="*60)
        
        if audio_path is None:
            video_name = Path(video_path).stem
            audio_path = str(Path(video_path).parent / f"{video_name}_audio.{self.output_format}")
            
        try:
            # Load video
            video = VideoFileClip(video_path)
            
            # Check if video has audio
            if video.audio is None:
                video.close()
                error_msg = (
                    f"Video '{Path(video_path).name}' has no audio track. "
                    "Please upload a video with audio to generate transcripts."
                )
                logger.error(f"❌ {error_msg}")
                raise ValueError(error_msg)
            
            # Extract audio using MoviePy first
            temp_audio = str(Path(audio_path).parent / f"temp_audio.wav")
            
            # MoviePy 2.x compatibility - no verbose/logger parameters
            video.audio.write_audiofile(temp_audio)
            video.close()
            
            # Convert to compressed format using pydub
            logger.info(f"Converting to {self.output_format.upper()} format...")
            audio = AudioSegment.from_wav(temp_audio)
            
            # Export with compression
            export_params = {
                "format": self.output_format,
                "bitrate": self.bitrate,
                "parameters": ["-ac", str(self.channels)]
            }
            
            if self.output_format == "ogg":
                export_params["codec"] = "libopus"
            
            audio.export(audio_path, **export_params)
            
            # Clean up temp file
            if os.path.exists(temp_audio):
                os.remove(temp_audio)
            
            # Get file size
            file_size = os.path.getsize(audio_path) / (1024 * 1024)
            logger.info(f"✅ Audio extracted: {file_size:.2f}MB")
            logger.info(f"   Saved to: {audio_path}")
            logger.info("="*60)
            
            return audio_path
            
        except ValueError:
            # Re-raise ValueError with our custom message
            raise
        except Exception as e:
            logger.error(f"Error extracting audio: {e}")
            raise
            
    def get_audio_duration(self, audio_path: str) -> float:
        """
        Get audio duration in seconds
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Duration in seconds
        """
        audio = AudioSegment.from_file(audio_path)
        return len(audio) / 1000.0