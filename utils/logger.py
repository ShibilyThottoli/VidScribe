"""Logging configuration"""

import logging
import sys
from pathlib import Path
import config


def setup_logger(name: str = None) -> logging.Logger:
    """
    Setup and configure logger
    
    Args:
        name: Logger name (uses root if None)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, config.LOG_LEVEL))
    
    # Create formatters
    detailed_formatter = logging.Formatter(config.LOG_FORMAT)
    simple_formatter = logging.Formatter('%(levelname)s - %(message)s')
    
    # Console handler (stdout) with UTF-8 encoding
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # File handler with UTF-8 encoding (FIX FOR WINDOWS)
    try:
        config.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(
            config.LOG_FILE,
            encoding='utf-8'  # ← Added UTF-8 encoding
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.error(f"Could not create log file: {e}")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get or create logger with given name"""
    return setup_logger(name)


# Setup root logger on import
setup_logger()