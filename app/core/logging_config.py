# Centralized logging configuration for the application
# Provides structured logging with proper formatting and handlers

import logging
import logging.config
import sys
from datetime import datetime
from pathlib import Path

def setup_logging():
    """
    Configure application-wide logging with proper formatting and handlers
    
    Sets up:
    - Console logging for development
    - File logging for production
    - Structured log format with timestamps
    - Different log levels for different components
    """
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Define log format
    log_format = {
        'format': '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
        'datefmt': '%Y-%m-%d %H:%M:%S'
    }
    
    # Logging configuration
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'detailed': log_format,
            'simple': {
                'format': '%(levelname)s | %(name)s | %(message)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': 'simple',
                'stream': sys.stdout
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'DEBUG',
                'formatter': 'detailed',
                'filename': log_dir / 'app.log',
                'maxBytes': 10 * 1024 * 1024,  # 10MB
                'backupCount': 5,
                'encoding': 'utf-8'
            },
            'error_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'ERROR',
                'formatter': 'detailed',
                'filename': log_dir / 'errors.log',
                'maxBytes': 10 * 1024 * 1024,  # 10MB
                'backupCount': 5,
                'encoding': 'utf-8'
            }
        },
        'loggers': {
            # Application loggers
            'app': {
                'level': 'DEBUG',
                'handlers': ['console', 'file', 'error_file'],
                'propagate': False
            },
            'app.core.exceptions': {
                'level': 'WARNING',
                'handlers': ['console', 'error_file'],
                'propagate': False
            },
            'app.crud': {
                'level': 'INFO',
                'handlers': ['console', 'file'],
                'propagate': False
            },
            'app.api': {
                'level': 'INFO',
                'handlers': ['console', 'file'],
                'propagate': False
            },
            # Database loggers
            'sqlalchemy.engine': {
                'level': 'WARNING',  # Only log warnings/errors, not all SQL
                'handlers': ['file'],
                'propagate': False
            },
            'sqlalchemy.pool': {
                'level': 'WARNING',
                'handlers': ['file'],
                'propagate': False
            },
            # Third-party loggers
            'uvicorn': {
                'level': 'INFO',
                'handlers': ['console'],
                'propagate': False
            },
            'uvicorn.error': {
                'level': 'INFO',
                'handlers': ['console', 'error_file'],
                'propagate': False
            },
            'uvicorn.access': {
                'level': 'INFO',
                'handlers': ['file'],
                'propagate': False
            },
            'fastapi': {
                'level': 'INFO',
                'handlers': ['console', 'file'],
                'propagate': False
            }
        },
        'root': {
            'level': 'INFO',
            'handlers': ['console', 'file']
        }
    }
    
    # Apply the configuration
    logging.config.dictConfig(config)
    
    # Log startup message
    logger = logging.getLogger('app')
    logger.info(f"Logging configured successfully at {datetime.now()}")
    logger.info(f"Log files will be written to: {log_dir.absolute()}")

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(f"app.{name}")

# Initialize logging when module is imported
setup_logging()