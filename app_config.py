"""
Configuration management for LibreAssistant backend
Centralizes environment variable handling and default values
"""

import os
from typing import Optional


class AppConfig:
    """Centralized configuration management"""
    
    def __init__(self):
        self._load_config()
    
    def _load_config(self):
        """Load configuration from environment variables with defaults"""
        # Flask/Backend Configuration
        self.flask_host = os.environ.get('FLASK_HOST', '0.0.0.0')
        self.flask_port = int(os.environ.get('FLASK_PORT', '5000'))
        self.flask_debug = os.environ.get('FLASK_DEBUG', 'False').lower() in ['true', '1', 'yes']
        
        # Ollama Configuration
        self.ollama_host = os.environ.get('OLLAMA_HOST', 'http://localhost:11434')
        self.ollama_api_timeout = float(os.environ.get('OLLAMA_API_TIMEOUT', '180'))
        
        # Application Configuration
        self.app_name = os.environ.get('APP_NAME', 'LibreAssistant')
        self.app_version = os.environ.get('APP_VERSION', '1.0.0')
        self.default_model = os.environ.get('DEFAULT_MODEL', '')
        
        # Plugin Configuration
        self.disable_plugin_autostart = os.environ.get('DISABLE_PLUGIN_AUTOSTART', '').lower() in ['true', '1', 'yes']
        
        # Development Settings
        self.log_level = os.environ.get('LOG_LEVEL', 'INFO')
        
        # API Configuration
        self.max_retries = int(os.environ.get('MAX_RETRIES', '3'))
        self.plugin_retries = int(os.environ.get('PLUGIN_RETRIES', '2'))
    
    def get_ollama_config(self) -> dict:
        """Get Ollama-specific configuration"""
        return {
            'host': self.ollama_host,
            'timeout': self.ollama_api_timeout
        }
    
    def get_flask_config(self) -> dict:
        """Get Flask-specific configuration"""
        return {
            'host': self.flask_host,
            'port': self.flask_port,
            'debug': self.flask_debug
        }
    
    def get_plugin_config(self) -> dict:
        """Get plugin-specific configuration"""
        return {
            'disable_autostart': self.disable_plugin_autostart,
            'max_retries': self.plugin_retries
        }


# Global configuration instance
app_config = AppConfig()


def get_config() -> AppConfig:
    """Get the global configuration instance"""
    return app_config


def get_server_url_with_fallback(request_arg: Optional[str] = None) -> str:
    """
    Get server URL with fallback chain:
    1. Request argument (query param)
    2. Environment variable
    3. Default from config
    """
    if request_arg:
        return request_arg
    return app_config.ollama_host


def get_timeout_with_fallback(request_arg: Optional[float] = None) -> float:
    """
    Get timeout with fallback chain:
    1. Request argument (query param)
    2. Environment variable
    3. Default from config
    """
    if request_arg is not None:
        return request_arg
    return app_config.ollama_api_timeout