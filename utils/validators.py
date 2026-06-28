"""Video validation utilities"""

import os
import cv2
import logging
from pathlib import Path
from typing import Tuple, Optional
import config

logger = logging.getLogger(__name__)


class VideoValidator:
    """Validate video files before processing"""
    
    def __init__(self):
        self.max_size = config.MAX_FILE_SIZE
        self.max_duration = config.MAX_VIDEO_DURATION
        self.allowed_extensions = config.ALLOWED_EXTENSIONS
    
    def validate_file(self, filepath: str) -> Tuple[bool, Optional[str]]:
        """
        Validate video file
        
        Args:
            filepath: Path to video file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check if file exists
            if not os.path.exists(filepath):
                return False, "File not found"
            
            # Check file extension
            is_valid, error = self.validate_extension(filepath)
            if not is_valid:
                return False, error
            
            # Check file size
            is_valid, error = self.validate_size(filepath)
            if not is_valid:
                return False, error
            
            # Check video duration
            is_valid, error = self.validate_duration(filepath)
            if not is_valid:
                return False, error
            
            logger.info(f"✅ Video validation passed: {filepath}")
            return True, None
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False, f"Validation error: {str(e)}"
    
    def validate_extension(self, filepath: str) -> Tuple[bool, Optional[str]]:
        """Check if file extension is allowed"""
        ext = Path(filepath).suffix.lower().replace('.', '')
        
        if ext not in self.allowed_extensions:
            allowed = ', '.join(self.allowed_extensions)
            return False, f"Invalid format. Allowed: {allowed}"
        
        return True, None
    
    def validate_size(self, filepath: str) -> Tuple[bool, Optional[str]]:
        """Check if file size is within limits"""
        file_size = os.path.getsize(filepath)
        
        if file_size > self.max_size:
            max_gb = self.max_size / (1024 ** 3)
            actual_gb = file_size / (1024 ** 3)
            return False, f"File too large ({actual_gb:.2f}GB). Max: {max_gb:.1f}GB"
        
        logger.info(f"File size: {file_size / (1024**2):.2f}MB")
        return True, None
    
    def validate_duration(self, filepath: str) -> Tuple[bool, Optional[str]]:
        """Check if video duration is within limits"""
        try:
            cap = cv2.VideoCapture(filepath)
            
            if not cap.isOpened():
                return False, "Cannot open video file"
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            
            if fps == 0:
                cap.release()
                return False, "Invalid video: FPS is 0"
            
            duration = frame_count / fps
            cap.release()
            
            if duration > self.max_duration:
                max_min = self.max_duration / 60
                actual_min = duration / 60
                return False, f"Video too long ({actual_min:.1f} min). Max: {max_min:.0f} min"
            
            logger.info(f"Video duration: {duration / 60:.2f} minutes")
            return True, None
            
        except Exception as e:
            logger.error(f"Error checking duration: {e}")
            return False, f"Cannot read video duration: {str(e)}"
    
    def get_video_info(self, filepath: str) -> dict:
        """Get detailed video information"""
        try:
            cap = cv2.VideoCapture(filepath)
            
            if not cap.isOpened():
                return {'error': 'Cannot open video'}
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = frame_count / fps if fps > 0 else 0
            
            cap.release()
            
            file_size = os.path.getsize(filepath)
            
            return {
                'duration_seconds': duration,
                'duration_formatted': f"{int(duration // 60)}:{int(duration % 60):02d}",
                'fps': fps,
                'frame_count': frame_count,
                'resolution': f"{width}x{height}",
                'width': width,
                'height': height,
                'file_size_bytes': file_size,
                'file_size_mb': file_size / (1024 ** 2),
                'format': Path(filepath).suffix.lower()
            }
            
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            return {'error': str(e)}


def validate_filename(filename: str) -> bool:
    """Check if filename is safe"""
    # Check for dangerous characters
    dangerous_chars = ['..', '/', '\\', '<', '>', ':', '"', '|', '?', '*']
    return not any(char in filename for char in dangerous_chars)


def allowed_file(filename: str) -> bool:
    """Quick check if file extension is allowed"""
    ext = Path(filename).suffix.lower().replace('.', '')
    return ext in config.ALLOWED_EXTENSIONS