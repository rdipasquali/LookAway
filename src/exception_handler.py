"""
Central Exception Handler for LookAway
Provides centralized exception logging and handling for the application.
"""

import os
import sys
import traceback
import logging
from pathlib import Path
from datetime import datetime
import threading
from typing import Optional, Any

class CentralExceptionHandler:
    """Centralized exception handler for the application."""
    
    def __init__(self, log_dir: Optional[Path] = None, enabled: bool = True):
        """
        Initialize the exception handler.
        
        Args:
            log_dir: Directory to store log files (default: logs/ in app directory)
            enabled: Whether exception logging is enabled
        """
        self.enabled = enabled
        self.log_dir = log_dir or self._get_default_log_dir()
        self.logger = None
        
        if self.enabled:
            self._setup_logger()
            self._install_handlers()
    
    def _get_default_log_dir(self) -> Path:
        """Get the default log directory."""
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            app_dir = Path(sys.executable).parent
        else:
            # Running as script
            app_dir = Path(__file__).parent.parent
        
        log_dir = app_dir / "logs"
        
        # Ensure log directory is created immediately and handle errors
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            # Test write access by creating a test file
            test_file = log_dir / ".write_test"
            test_file.write_text("test")
            test_file.unlink()  # Delete test file
        except Exception as e:
            # If we can't create in the app directory, fall back to a temp location
            import tempfile
            fallback_dir = Path(tempfile.gettempdir()) / "LookAway" / "logs"
            try:
                fallback_dir.mkdir(parents=True, exist_ok=True)
                log_dir = fallback_dir
                print(f"Warning: Using fallback log directory: {log_dir} (Original error: {e})")
            except Exception as fallback_error:
                print(f"Critical: Cannot create log directory anywhere. Original: {e}, Fallback: {fallback_error}")
                # Return the original path anyway, let it fail later if needed
        
        return log_dir
    
    def _setup_logger(self):
        """Setup the exception logger."""
        if not self.enabled:
            return
        
        # Create log directory if it doesn't exist
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger('LookAway_Exceptions')
        self.logger.setLevel(logging.DEBUG)  # Changed to DEBUG to catch more
        
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # Create file handler with rotation
        log_file = self.log_dir / "exceptions.log"
        
        # Use a simple file handler (avoiding RotatingFileHandler for exe compatibility)
        try:
            # If log file is too large (>1MB), archive it
            if log_file.exists() and log_file.stat().st_size > 1024 * 1024:
                archive_file = self.log_dir / f"exceptions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                try:
                    log_file.rename(archive_file)
                except Exception:
                    # If rename fails, just truncate
                    log_file.write_text("")
            
            file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
            
            # Create formatter
            formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            
            # Add handler to logger
            self.logger.addHandler(file_handler)
            
            # Force flush after setup
            file_handler.flush()
            
            # Log startup with more details
            self.logger.error("=" * 80)
            self.logger.error(f"LookAway Exception Logging Started - PID: {os.getpid()}")
            self.logger.error(f"Executable: {sys.executable}")
            self.logger.error(f"Arguments: {sys.argv}")
            self.logger.error(f"Frozen: {getattr(sys, 'frozen', False)}")
            self.logger.error(f"Platform: {sys.platform}")
            self.logger.error(f"Python Version: {sys.version}")
            self.logger.error(f"Working Directory: {os.getcwd()}")
            self.logger.error(f"Log Directory: {self.log_dir}")
            self.logger.error("=" * 80)
            
            # Force flush after startup log
            file_handler.flush()
            
        except Exception as e:
            # If logging setup fails, disable logging but print details
            print(f"Failed to setup exception logging: {e}")
            print(f"Log directory attempted: {self.log_dir}")
            print(f"Current working directory: {os.getcwd()}")
            self.enabled = False
    
    def _install_handlers(self):
        """Install exception handlers."""
        if not self.enabled:
            return
        
        # Install global exception handler
        sys.excepthook = self._handle_exception
        
        # Install threading exception handler (Python 3.8+)
        if hasattr(threading, 'excepthook'):
            threading.excepthook = self._handle_thread_exception
    
    def _handle_exception(self, exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions."""
        if not self.enabled or not self.logger:
            # Fall back to default behavior
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        try:
            # Don't log KeyboardInterrupt
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            
            # Format exception
            tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
            tb_text = ''.join(tb_lines)
            
            # Log exception
            self.logger.error("UNCAUGHT EXCEPTION:")
            self.logger.error(f"Type: {exc_type.__name__}")
            self.logger.error(f"Message: {str(exc_value)}")
            self.logger.error(f"Traceback:\n{tb_text}")
            
            # Also log to stderr if not frozen (for development)
            if not getattr(sys, 'frozen', False):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
        
        except Exception as log_error:
            # If logging fails, fall back to default
            print(f"Exception logging failed: {log_error}")
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
    
    def _handle_thread_exception(self, args):
        """Handle uncaught thread exceptions."""
        if not self.enabled or not self.logger:
            return
        
        try:
            exc_type = args.exc_type
            exc_value = args.exc_value
            exc_traceback = args.exc_traceback
            thread = args.thread
            
            # Format exception
            tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
            tb_text = ''.join(tb_lines)
            
            # Log thread exception
            self.logger.error("THREAD EXCEPTION:")
            self.logger.error(f"Thread: {thread.name} (ID: {thread.ident})")
            self.logger.error(f"Type: {exc_type.__name__}")
            self.logger.error(f"Message: {str(exc_value)}")
            self.logger.error(f"Traceback:\n{tb_text}")
        
        except Exception as log_error:
            print(f"Thread exception logging failed: {log_error}")
    
    def log_exception(self, exc_info: Any = None, context: str = ""):
        """
        Manually log an exception.
        
        Args:
            exc_info: Exception info (default: current exception)
            context: Additional context information
        """
        if not self.enabled or not self.logger:
            return
        
        try:
            if exc_info is None:
                exc_info = sys.exc_info()
            
            if exc_info[0] is None:
                # No current exception
                return
            
            exc_type, exc_value, exc_traceback = exc_info
            
            # Format exception
            tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
            tb_text = ''.join(tb_lines)
            
            # Log exception with context
            self.logger.error("LOGGED EXCEPTION:")
            if context:
                self.logger.error(f"Context: {context}")
            self.logger.error(f"Type: {exc_type.__name__}")
            self.logger.error(f"Message: {str(exc_value)}")
            self.logger.error(f"Traceback:\n{tb_text}")
        
        except Exception as log_error:
            print(f"Manual exception logging failed: {log_error}")
    
    def log_critical_error(self, message: str, exc_info: Any = None):
        """
        Log a critical error that might cause the application to crash.
        
        Args:
            message: Description of the critical error
            exc_info: Optional exception info
        """
        if not self.enabled or not self.logger:
            return
        
        try:
            self.logger.error("CRITICAL ERROR:")
            self.logger.error(f"Message: {message}")
            
            if exc_info:
                if exc_info is True:
                    exc_info = sys.exc_info()
                
                if exc_info[0] is not None:
                    exc_type, exc_value, exc_traceback = exc_info
                    tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
                    tb_text = ''.join(tb_lines)
                    self.logger.error(f"Exception: {exc_type.__name__}: {str(exc_value)}")
                    self.logger.error(f"Traceback:\n{tb_text}")
            
            # Force flush after critical errors
            self.flush_logs()
        
        except Exception as log_error:
            print(f"Critical error logging failed: {log_error}")
    
    def flush_logs(self):
        """Force flush all log handlers to ensure data is written to disk."""
        if not self.enabled or not self.logger:
            return
        
        try:
            for handler in self.logger.handlers:
                if hasattr(handler, 'flush'):
                    handler.flush()
        except Exception as e:
            print(f"Log flush failed: {e}")
    
    def is_enabled(self) -> bool:
        """Check if exception logging is enabled."""
        return self.enabled
    
    def get_log_file(self) -> Optional[Path]:
        """Get the path to the current log file."""
        if self.enabled:
            return self.log_dir / "exceptions.log"
        return None
    
    def cleanup(self):
        """Cleanup resources and restore default handlers."""
        try:
            if self.logger:
                # Close all handlers
                for handler in self.logger.handlers[:]:
                    handler.close()
                    self.logger.removeHandler(handler)
            
            # Restore default exception handlers
            sys.excepthook = sys.__excepthook__
            if hasattr(threading, 'excepthook'):
                threading.excepthook = threading.__excepthook__
        
        except Exception as e:
            print(f"Exception handler cleanup failed: {e}")


# Global exception handler instance
_global_exception_handler: Optional[CentralExceptionHandler] = None

def initialize_exception_handler(enabled: bool = True, log_dir: Optional[Path] = None) -> CentralExceptionHandler:
    """
    Initialize the global exception handler.
    
    Args:
        enabled: Whether to enable exception logging
        log_dir: Custom log directory (optional)
        
    Returns:
        The initialized exception handler
    """
    global _global_exception_handler
    
    if _global_exception_handler is not None:
        _global_exception_handler.cleanup()
    
    _global_exception_handler = CentralExceptionHandler(log_dir=log_dir, enabled=enabled)
    return _global_exception_handler

def get_exception_handler() -> Optional[CentralExceptionHandler]:
    """Get the global exception handler instance."""
    return _global_exception_handler

def log_exception(exc_info: Any = None, context: str = ""):
    """Log an exception using the global handler."""
    if _global_exception_handler:
        _global_exception_handler.log_exception(exc_info, context)

def log_critical_error(message: str, exc_info: Any = None):
    """Log a critical error using the global handler."""
    if _global_exception_handler:
        _global_exception_handler.log_critical_error(message, exc_info)

def flush_exception_logs():
    """Force flush exception logs using the global handler."""
    if _global_exception_handler:
        _global_exception_handler.flush_logs()

def cleanup_exception_handler():
    """Cleanup the global exception handler."""
    global _global_exception_handler
    if _global_exception_handler:
        _global_exception_handler.cleanup()
        _global_exception_handler = None