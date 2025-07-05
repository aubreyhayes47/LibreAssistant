"""
Structured logging configuration for LibreAssistant.
"""

import os
import logging
import logging.handlers
from datetime import datetime
from typing import Optional
import json


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging."""
    
    def format(self, record):
        """Format log record as structured JSON."""
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'session_id'):
            log_entry['session_id'] = record.session_id
        if hasattr(record, 'command'):
            log_entry['command'] = record.command
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)


class LibreAssistantLogger:
    """Centralized logging configuration for LibreAssistant."""
    
    def __init__(self, log_dir: Optional[str] = None):
        """Initialize logger with optional custom log directory."""
        if log_dir is None:
            # Default to backend directory
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            log_dir = os.path.join(backend_dir, 'logs')
        
        self.log_dir = log_dir
        self.ensure_log_directory()
        
        # Configure different log files for different components
        self.log_files = {
            'main': os.path.join(log_dir, 'main.log'),
            'database': os.path.join(log_dir, 'database.log'),
            'llm': os.path.join(log_dir, 'llm.log'),
            'web_scraping': os.path.join(log_dir, 'web_scraping.log'),
            'errors': os.path.join(log_dir, 'errors.log')
        }
        
        self.loggers = {}
        self._setup_loggers()
    
    def ensure_log_directory(self):
        """Ensure log directory exists."""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir, exist_ok=True)
    
    def _setup_loggers(self):
        """Set up different loggers for different components."""
        # Main application logger
        self._create_logger(
            'libreassistant.main',
            self.log_files['main'],
            logging.INFO
        )
        
        # Database operations logger
        self._create_logger(
            'libreassistant.database',
            self.log_files['database'],
            logging.INFO
        )
        
        # LLM operations logger
        self._create_logger(
            'libreassistant.llm',
            self.log_files['llm'],
            logging.INFO
        )
        
        # Web scraping logger
        self._create_logger(
            'libreassistant.web',
            self.log_files['web_scraping'],
            logging.INFO
        )
        
        # Error logger (for all error-level messages)
        self._create_logger(
            'libreassistant.errors',
            self.log_files['errors'],
            logging.ERROR
        )
        
        # Configure root logger to avoid stdout conflicts with Tauri
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # Remove any existing handlers to avoid conflicts
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Add file handler for general logging
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_files['main'],
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(file_handler)
    
    def _create_logger(self, name: str, log_file: str, level: int):
        """Create a logger with file rotation."""
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # Remove existing handlers to avoid duplicates
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Create rotating file handler
        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB per file
            backupCount=5  # Keep 5 backup files
        )
        
        # Use structured formatter
        formatter = StructuredFormatter()
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        logger.propagate = False  # Don't propagate to root logger
        
        self.loggers[name] = logger
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger by name."""
        full_name = f'libreassistant.{name}'
        if full_name in self.loggers:
            return self.loggers[full_name]
        return logging.getLogger(full_name)
    
    def log_command_start(self, command: str, payload: dict, session_id: str = None):
        """Log the start of a command execution."""
        logger = self.get_logger('main')
        extra = {'command': command, 'session_id': session_id}
        logger.info(f"Command '{command}' started", extra=extra)
    
    def log_command_success(self, command: str, duration: float, session_id: str = None):
        """Log successful command completion."""
        logger = self.get_logger('main')
        extra = {'command': command, 'session_id': session_id, 'duration': duration}
        logger.info(f"Command '{command}' completed successfully in {duration:.2f}s", extra=extra)
    
    def log_command_error(self, command: str, error: str, session_id: str = None):
        """Log command execution error."""
        logger = self.get_logger('errors')
        extra = {'command': command, 'session_id': session_id}
        logger.error(f"Command '{command}' failed: {error}", extra=extra)
    
    def log_database_operation(self, operation: str, table: str, success: bool, details: str = None):
        """Log database operations."""
        logger = self.get_logger('database')
        level = logging.INFO if success else logging.ERROR
        message = f"Database {operation} on {table}: {'SUCCESS' if success else 'FAILED'}"
        if details:
            message += f" - {details}"
        logger.log(level, message)
    
    def log_llm_interaction(self, model: str, prompt_length: int, response_length: int, duration: float):
        """Log LLM interactions."""
        logger = self.get_logger('llm')
        logger.info(
            f"LLM interaction: model={model}, prompt_length={prompt_length}, "
            f"response_length={response_length}, duration={duration:.2f}s"
        )
    
    def log_web_request(self, url: str, status_code: int, duration: float):
        """Log web scraping requests."""
        logger = self.get_logger('web')
        logger.info(f"Web request: {url} -> {status_code} ({duration:.2f}s)")


# Global logger instance
_logger_instance: Optional[LibreAssistantLogger] = None


def init_logging(log_dir: Optional[str] = None) -> LibreAssistantLogger:
    """Initialize global logging configuration."""
    global _logger_instance
    _logger_instance = LibreAssistantLogger(log_dir)
    return _logger_instance


def get_logger(name: str = 'main') -> logging.Logger:
    """Get a logger instance."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = LibreAssistantLogger()
    return _logger_instance.get_logger(name)


def log_command_start(command: str, payload: dict, session_id: str = None):
    """Log command start."""
    global _logger_instance
    if _logger_instance:
        _logger_instance.log_command_start(command, payload, session_id)


def log_command_success(command: str, duration: float, session_id: str = None):
    """Log command success."""
    global _logger_instance
    if _logger_instance:
        _logger_instance.log_command_success(command, duration, session_id)


def log_command_error(command: str, error: str, session_id: str = None):
    """Log command error."""
    global _logger_instance
    if _logger_instance:
        _logger_instance.log_command_error(command, error, session_id)
