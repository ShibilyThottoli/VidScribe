"""Helper utility functions"""

import os
import re
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import config


def allowed_file(filename: str, allowed_extensions: set = None) -> bool:
    """
    Check if filename has allowed extension
    
    Args:
        filename: Name of file to check
        allowed_extensions: Set of allowed extensions (uses config default if None)
        
    Returns:
        True if extension is allowed
    """
    if allowed_extensions is None:
        allowed_extensions = config.ALLOWED_EXTENSIONS
    
    ext = Path(filename).suffix.lower().replace('.', '')
    return ext in allowed_extensions


def get_unique_filename(filename: str) -> str:
    """
    Generate unique filename with timestamp
    
    Args:
        filename: Original filename
        
    Returns:
        Unique filename
    """
    name = Path(filename).stem
    ext = Path(filename).suffix
    
    # Remove special characters
    name = re.sub(r'[^\w\-_]', '_', name)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{name}_{timestamp}{ext}"


def cleanup_temp_files(*filepaths: str):
    """
    Delete temporary files
    
    Args:
        *filepaths: Variable number of file paths to delete
    """
    for filepath in filepaths:
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            print(f"Error deleting {filepath}: {e}")


def format_timestamp(seconds: float) -> str:
    """
    Format seconds as MM:SS or HH:MM:SS
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted timestamp string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def sanitize_filename(filename: str) -> str:
    """
    Remove dangerous characters from filename
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove path separators and dangerous characters
    name = Path(filename).name
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    
    # Remove leading/trailing dots and spaces
    name = name.strip('. ')
    
    return name


def parse_video_format(filepath: str) -> dict:
    """
    Extract format information from video filepath
    
    Args:
        filepath: Path to video file
        
    Returns:
        Dictionary with format info
    """
    path = Path(filepath)
    
    return {
        'filename': path.name,
        'stem': path.stem,
        'extension': path.suffix.lower(),
        'format': path.suffix.lower().replace('.', ''),
        'directory': str(path.parent)
    }


def create_progress_message(current: int, total: int, task: str = "") -> str:
    """
    Create progress message
    
    Args:
        current: Current step number
        total: Total number of steps
        task: Description of current task
        
    Returns:
        Formatted progress message
    """
    percentage = int((current / total) * 100)
    bar_length = 20
    filled = int(bar_length * current / total)
    bar = '█' * filled + '░' * (bar_length - filled)
    
    message = f"[{bar}] {percentage}% ({current}/{total})"
    if task:
        message += f" - {task}"
    
    return message


def estimate_processing_time(duration_seconds: float) -> str:
    """
    Estimate processing time based on video duration
    
    Args:
        duration_seconds: Video duration in seconds
        
    Returns:
        Estimated time string
    """
    # Rough estimate: 1 minute of video = 30 seconds processing
    estimated_seconds = duration_seconds / 2
    
    if estimated_seconds < 60:
        return f"~{int(estimated_seconds)} seconds"
    else:
        minutes = int(estimated_seconds / 60)
        return f"~{minutes} minute{'s' if minutes > 1 else ''}"