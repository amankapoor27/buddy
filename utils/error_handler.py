import sys
import traceback
import threading
from loguru import logger

class ErrorHandler:
    """Global error handler for crash recovery and logging."""
    
    @staticmethod
    def init():
        """Initialize global error handling."""
        sys.excepthook = ErrorHandler.handle_exception
        threading.excepthook = ErrorHandler.handle_thread_exception
    
    @staticmethod
    def handle_exception(exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions.
        
        Args:
            exc_type: Exception type
            exc_value: Exception value
            exc_traceback: Exception traceback
        """
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        logger.error("Uncaught exception:", exc_info=(exc_type, exc_value, exc_traceback))
    
    @staticmethod
    def handle_thread_exception(args):
        """Handle uncaught thread exceptions.
        
        Args:
            args: Thread exception arguments
        """
        if args.exc_type == SystemExit:
            return
        
        logger.error(f"Uncaught thread exception in {args.thread.name}:",
                    exc_info=(args.exc_type, args.exc_value, args.exc_traceback))