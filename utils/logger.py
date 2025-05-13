import os
import sys
from loguru import logger

def setup_logger(log_file=None):
    """Configure logger for the application
    
    Args:
        log_file (str, optional): Path to log file. Defaults to None.
    """
    # Remove default logger
    logger.remove()
    
    # Determine log file path if not provided
    if log_file is None:
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, 'buddy.log')
    
    # Add console logger
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    
    # Add file logger
    logger.add(
        log_file,
        rotation="10 MB",
        retention="1 week",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG"
    )
    
    return logger