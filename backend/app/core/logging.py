"""
Logging configuration for RAG Fortress
"""
import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
from app.config import settings


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        if sys.stdout.isatty():  # Only use colors if outputting to terminal
            log_color = self.COLORS.get(record.levelname, self.RESET)
            record.levelname = f"{log_color}{record.levelname}{self.RESET}"
            record.name = f"\033[94m{record.name}{self.RESET}"  # Blue for logger name
        return super().format(record)


class PlainFormatter(logging.Formatter):
    """Plain formatter without colors for file output"""
    
    def format(self, record):
        # Ensure no color codes in record
        if '\033[' in record.levelname:
            record.levelname = record.levelname.replace('\033[32m', '').replace('\033[33m', '').replace('\033[31m', '').replace('\033[35m', '').replace('\033[36m', '').replace('\033[0m', '').replace('\033[94m', '')
        if '\033[' in record.name:
            record.name = record.name.replace('\033[94m', '').replace('\033[0m', '')
        return super().format(record)


def setup_logging(
    name: Optional[str] = None,
    log_level: Optional[str] = None,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Set up logging configuration
    
    Args:
        name: Logger name (defaults to app name)
        log_level: Logging level (defaults to settings.LOG_LEVEL)
        log_file: Log file path (defaults to settings.LOG_FILE)
    
    Returns:
        Configured logger instance
    """
    logger_name = name or settings.APP_NAME
    logger = logging.getLogger(logger_name)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    level = log_level or settings.LOG_LEVEL
    logger.setLevel(getattr(logging, level.upper()))
    
    # Console handler with colored output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    if settings.ENVIRONMENT == "production":
        # Simple format for production
        console_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        # Detailed format with colors for development
        console_format = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%H:%M:%S'
        )
    
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File handler (rotating) - WITHOUT colors
    log_file_path = log_file or settings.LOG_FILE
    if log_file_path:
        try:
            # Create logs directory if it doesn't exist
            log_path = Path(log_file_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Rotating file handler (10MB per file, keep 5 backups)
            file_handler = logging.handlers.RotatingFileHandler(
                str(log_path),  # Convert Path to string for compatibility
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding='utf-8',
                delay=False  # Don't delay file creation
            )
            file_handler.setLevel(logging.DEBUG)
            
            # JSON-like format for file logs (easier to parse) - NO COLORS via PlainFormatter
            file_format = PlainFormatter(
                '{"time": "%(asctime)s", "name": "%(name)s", "level": "%(levelname)s", '
                '"function": "%(funcName)s", "line": %(lineno)d, "message": "%(message)s"}',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_format)
            logger.addHandler(file_handler)
        except Exception as e:
            # If file handler fails, still output to console
            console_handler.emit(logging.LogRecord(
                logger_name, logging.WARNING,
                __file__, 0,
                f"Failed to set up file logging: {e}",
                (), None
            ))
    
    # Don't propagate to root logger
    logger.propagate = False
    
    return logger


_default_logger = None


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance
    
    Args:
        name: Logger name (usually __name__ of the module)
    
    Returns:
        Logger instance
    """
    global _default_logger
    
    # Ensure default logger is initialized
    if _default_logger is None:
        _default_logger = setup_logging()
    
    # If it's a module name, just get that logger
    if '.' in name:
        logger = logging.getLogger(name)
    else:
        # Otherwise, namespace it under the app
        logger = logging.getLogger(f"{settings.APP_NAME}.{name}")
    
    # If logger has no handlers, add handlers from default logger
    if not logger.handlers:
        for handler in _default_logger.handlers:
            logger.addHandler(handler)
        logger.setLevel(_default_logger.level)
    
    # Don't propagate to root logger
    logger.propagate = False
    
    return logger


# Initialize default logger on first import
try:
    default_logger = setup_logging()
except Exception as e:
    # If setup fails, create a minimal console logger
    print(f"Warning: Failed to initialize logging system: {e}")
    default_logger = logging.getLogger(settings.APP_NAME)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    default_logger.addHandler(console_handler)
    default_logger.setLevel(logging.INFO)


# Suppress noisy third-party loggers
def configure_third_party_loggers():
    """Configure logging levels for third-party libraries"""
    noisy_loggers = [
        'httpx',
        'httpcore',
        'urllib3',
        'chromadb',
        'sentence_transformers',
        'transformers',
        'torch',
    ]
    
    for logger_name in noisy_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)


# Configure on import
configure_third_party_loggers()


__all__ = ['setup_logging', 'get_logger', 'default_logger']
