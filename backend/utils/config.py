"""
Configuration management for LibreAssistant.
"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class DatabaseConfig:
    """Database configuration settings."""

    path: Optional[str] = None
    backup_enabled: bool = True
    backup_interval_hours: int = 24
    max_backup_files: int = 7
    wal_mode: bool = True

    def get_db_path(self) -> str:
        """Get the database file path."""
        if self.path:
            return self.path

        # Default to backend directory
        backend_dir = Path(__file__).parent.parent
        return str(backend_dir / "libreassistant.db")


@dataclass
class LLMConfig:
    """LLM configuration settings."""

    ollama_host: str = "http://localhost:11434"
    default_model: str = "phi3:mini"
    max_context_length: int = 4096
    temperature: float = 0.7
    timeout_seconds: int = 120
    retry_attempts: int = 3
    stream_responses: bool = True

    def validate(self) -> bool:
        """Validate LLM configuration."""
        return (
            self.temperature >= 0.0
            and self.temperature <= 2.0
            and self.max_context_length > 0
            and self.timeout_seconds > 0
            and self.retry_attempts >= 0
        )


@dataclass
class WebScrapingConfig:
    """Web scraping configuration settings."""

    user_agent: str = "LibreAssistant/1.0 (Privacy-focused AI Assistant)"
    request_timeout: int = 30
    max_page_size: int = 10 * 1024 * 1024  # 10MB
    respect_robots_txt: bool = True
    rate_limit_delay: float = 1.0  # seconds between requests
    max_retries: int = 3
    javascript_enabled: bool = True

    def validate(self) -> bool:
        """Validate web scraping configuration."""
        return (
            self.request_timeout > 0
            and self.max_page_size > 0
            and self.rate_limit_delay >= 0
            and self.max_retries >= 0
        )


@dataclass
class SecurityConfig:
    """Security configuration settings."""

    encryption_enabled: bool = True
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    allowed_domains: list = field(default_factory=list)
    blocked_domains: list = field(default_factory=list)
    sandbox_mode: bool = True

    def is_domain_allowed(self, domain: str) -> bool:
        """Check if a domain is allowed."""
        if domain in self.blocked_domains:
            return False

        if not self.allowed_domains:
            return True  # Allow all if no restrictions

        return domain in self.allowed_domains


@dataclass
class LoggingConfig:
    """Logging configuration settings."""

    log_level: str = "INFO"
    log_dir: Optional[str] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    structured_logging: bool = True

    def get_log_dir(self) -> str:
        """Get the log directory path."""
        if self.log_dir:
            return self.log_dir

        # Default to backend/logs directory
        backend_dir = Path(__file__).parent.parent
        return str(backend_dir / "logs")


@dataclass
class LibreAssistantConfig:
    """Main configuration class for LibreAssistant."""

    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    web_scraping: WebScrapingConfig = field(default_factory=WebScrapingConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    # Application settings
    app_name: str = "LibreAssistant"
    version: str = "0.1.0"
    debug_mode: bool = False
    data_retention_days: int = 365

    def validate(self) -> tuple[bool, list[str]]:
        """Validate entire configuration."""
        errors = []

        if not self.llm.validate():
            errors.append("Invalid LLM configuration")

        if not self.web_scraping.validate():
            errors.append("Invalid web scraping configuration")

        if self.data_retention_days <= 0:
            errors.append("Data retention days must be positive")

        return len(errors) == 0, errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""

        def _convert_dataclass(obj):
            if hasattr(obj, "__dataclass_fields__"):
                return {k: _convert_dataclass(v) for k, v in obj.__dict__.items()}
            elif isinstance(obj, list):
                return [_convert_dataclass(item) for item in obj]
            else:
                return obj

        return _convert_dataclass(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LibreAssistantConfig":
        """Create configuration from dictionary."""
        config = cls()

        if "database" in data:
            config.database = DatabaseConfig(**data["database"])

        if "llm" in data:
            config.llm = LLMConfig(**data["llm"])

        if "web_scraping" in data:
            config.web_scraping = WebScrapingConfig(**data["web_scraping"])

        if "security" in data:
            config.security = SecurityConfig(**data["security"])

        if "logging" in data:
            config.logging = LoggingConfig(**data["logging"])

        # Update top-level fields
        for key in ["app_name", "version", "debug_mode", "data_retention_days"]:
            if key in data:
                setattr(config, key, data[key])

        return config


class ConfigManager:
    """Manages configuration loading and saving."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize config manager with optional custom path."""
        if config_path is None:
            backend_dir = Path(__file__).parent.parent
            config_path = backend_dir / "config.json"

        self.config_path = Path(config_path)
        self._config: Optional[LibreAssistantConfig] = None

    def load_config(self) -> LibreAssistantConfig:
        """Load configuration from file or environment variables."""
        # Start with default configuration
        config = LibreAssistantConfig()

        # Load from file if it exists
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                config = LibreAssistantConfig.from_dict(data)
            except Exception as e:
                print(f"Warning: Failed to load config file: {e}")

        # Override with environment variables
        config = self._apply_env_overrides(config)

        # Validate configuration
        is_valid, errors = config.validate()
        if not is_valid:
            raise ValueError(f"Invalid configuration: {', '.join(errors)}")

        self._config = config
        return config

    def save_config(self, config: LibreAssistantConfig):
        """Save configuration to file."""
        try:
            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)

            self._config = config
        except Exception as e:
            raise RuntimeError(f"Failed to save configuration: {e}")

    def get_config(self) -> LibreAssistantConfig:
        """Get current configuration, loading if necessary."""
        if self._config is None:
            return self.load_config()
        return self._config

    def _apply_env_overrides(
        self, config: LibreAssistantConfig
    ) -> LibreAssistantConfig:
        """Apply environment variable overrides."""
        # Database overrides
        if os.getenv("LIBREASSISTANT_DB_PATH"):
            config.database.path = os.getenv("LIBREASSISTANT_DB_PATH")

        # LLM overrides
        if os.getenv("OLLAMA_HOST"):
            config.llm.ollama_host = os.getenv("OLLAMA_HOST")

        if os.getenv("LIBREASSISTANT_LLM_MODEL"):
            config.llm.default_model = os.getenv("LIBREASSISTANT_LLM_MODEL")

        if os.getenv("LIBREASSISTANT_LLM_TEMPERATURE"):
            try:
                config.llm.temperature = float(
                    os.getenv("LIBREASSISTANT_LLM_TEMPERATURE")
                )
            except ValueError:
                pass

        # Debug mode
        if os.getenv("LIBREASSISTANT_DEBUG"):
            config.debug_mode = os.getenv("LIBREASSISTANT_DEBUG").lower() in (
                "true",
                "1",
                "yes",
            )

        # Logging
        if os.getenv("LIBREASSISTANT_LOG_LEVEL"):
            config.logging.log_level = os.getenv("LIBREASSISTANT_LOG_LEVEL")

        if os.getenv("LIBREASSISTANT_LOG_DIR"):
            config.logging.log_dir = os.getenv("LIBREASSISTANT_LOG_DIR")

        return config


# Global configuration manager
_config_manager: Optional[ConfigManager] = None


def init_config(config_path: Optional[str] = None) -> LibreAssistantConfig:
    """Initialize global configuration."""
    global _config_manager
    _config_manager = ConfigManager(config_path)
    return _config_manager.load_config()


def get_config() -> LibreAssistantConfig:
    """Get current configuration."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager.get_config()


def save_config(config: LibreAssistantConfig):
    """Save configuration."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    _config_manager.save_config(config)
