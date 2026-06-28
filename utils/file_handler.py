"""File handling utilities"""

import os
import shutil
import time
from pathlib import Path
from datetime import datetime, timedelta
import logging
from typing import List
import config

logger = logging.getLogger(__name__)


class FileHandler:
    """Handle file operations"""
    
    @staticmethod
    def save_upload(file, filename: str) -> str:
        """
        Save uploaded file
        
        Args:
            file: FileStorage object from Flask
            filename: Secure filename
            
        Returns:
            Full path to saved file
        """
        filepath = config.get_upload_path(filename)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        file.save(str(filepath))
        logger.info(f"✅ File saved: {filepath}")
        
        return str(filepath)
    
    @staticmethod
    def delete_file(filepath: str) -> bool:
        """Delete a single file"""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"🗑️  Deleted: {filepath}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file {filepath}: {e}")
            return False
    
    @staticmethod
    def delete_directory(dirpath: str) -> bool:
        """Delete directory and all contents"""
        try:
            if os.path.exists(dirpath):
                shutil.rmtree(dirpath)
                logger.info(f"🗑️  Deleted directory: {dirpath}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting directory {dirpath}: {e}")
            return False
    
    @staticmethod
    def cleanup_temp_files(output_name: str = None):
        """
        Clean up temporary files
        
        Args:
            output_name: Specific output to clean, or None for all old files
        """
        try:
            if output_name:
                # Clean specific output
                temp_dir = config.TEMP_FOLDER / output_name
                FileHandler.delete_directory(str(temp_dir))
            else:
                # Clean all old temp files
                if config.TEMP_FOLDER.exists():
                    for item in config.TEMP_FOLDER.iterdir():
                        if item.is_dir():
                            FileHandler.delete_directory(str(item))
                        else:
                            FileHandler.delete_file(str(item))
                            
        except Exception as e:
            logger.error(f"Error cleaning temp files: {e}")
    
    @staticmethod
    def cleanup_old_outputs(hours: int = None):
        """
        Delete output files older than specified hours
        
        Args:
            hours: Age threshold in hours (uses config default if None)
        """
        if hours is None:
            hours = config.KEEP_OUTPUTS_HOURS
        
        try:
            cutoff_time = time.time() - (hours * 3600)
            deleted_count = 0
            
            for folder in [config.OUTPUT_FOLDER, config.UPLOAD_FOLDER]:
                if not folder.exists():
                    continue
                    
                for filepath in folder.iterdir():
                    if filepath.is_file():
                        file_age = os.path.getmtime(filepath)
                        if file_age < cutoff_time:
                            FileHandler.delete_file(str(filepath))
                            deleted_count += 1
            
            if deleted_count > 0:
                logger.info(f"🗑️  Cleaned up {deleted_count} old files")
                
        except Exception as e:
            logger.error(f"Error cleaning old outputs: {e}")
    
    @staticmethod
    def cleanup_upload(filepath: str):
        """Delete uploaded video file"""
        if config.AUTO_DELETE_UPLOADS:
            FileHandler.delete_file(filepath)
    
    @staticmethod
    def get_file_age(filepath: str) -> float:
        """Get file age in hours"""
        if not os.path.exists(filepath):
            return 0
        
        file_time = os.path.getmtime(filepath)
        current_time = time.time()
        age_seconds = current_time - file_time
        
        return age_seconds / 3600  # Convert to hours
    
    @staticmethod
    def ensure_directories():
        """Ensure all required directories exist"""
        directories = [
            config.UPLOAD_FOLDER,
            config.OUTPUT_FOLDER,
            config.TEMP_FOLDER,
            config.LOG_FILE.parent
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def get_available_outputs() -> List[dict]:
        """Get list of available output files"""
        outputs = []
        
        if config.OUTPUT_FOLDER.exists():
            for filepath in config.OUTPUT_FOLDER.iterdir():
                if filepath.is_file():
                    outputs.append({
                        'filename': filepath.name,
                        'path': str(filepath),
                        'size_mb': filepath.stat().st_size / (1024 ** 2),
                        'created': datetime.fromtimestamp(filepath.stat().st_mtime),
                        'age_hours': FileHandler.get_file_age(str(filepath))
                    })
        
        return outputs


def get_unique_filename(filename: str) -> str:
    """
    Generate unique filename with timestamp
    
    Args:
        filename: Original filename
        
    Returns:
        Unique filename with timestamp
    """
    name = Path(filename).stem
    ext = Path(filename).suffix
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    return f"{name}_{timestamp}{ext}"


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"