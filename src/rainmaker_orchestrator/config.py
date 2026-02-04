import logging
import os
from typing import Optional

logger: logging.Logger = logging.getLogger("config")

class ConfigManager:
    """Centralized configuration management with environment variable support."""

    def __init__(self, config_file: str = ".env") -> None:
        self.config_file: str = config_file
        if not os.path.exists(config_file):
            logger.error("Configuration file %s does not exist", config_file)
            raise FileNotFoundError(f"Config file {config_file} does not exist")
        
        try:
            from dotenv import load_dotenv
            load_dotenv(config_file)
            logger.info("Configuration loaded from %s", config_file)
        except ImportError:
            logger.warning("python-dotenv not available, using environment variables only")

    def get(self, key: str, default: str | None = None) -> str | None:
        value: str | None = os.getenv(key)
        if value is None:
            return default
        try:
            return int(value) if key.upper().endswith("_KEY") or key.upper().endswith("_TOKEN") else value
        except ValueError:
            logger.warning("Invalid configuration: %s=%s, using default=%s", key, value, default)
            return default

    def get_int(self, key: str, default: int = 0) -> int:
        value: Optional[str] = self.get(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            logger.error("Invalid integer configuration: %s=%s, using default=%d", key, value, default)
            raise ValueError(f"Invalid integer configuration: {key}={value}")