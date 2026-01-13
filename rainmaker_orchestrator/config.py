import os
import logging
from typing import Optional

logger: logging.Logger = logging.getLogger("config")


class ConfigManager:
    """Centralized configuration management with environment variable support."""

    def __init__(self, config_file: str = ".env") -> None:
        """Initialize configuration from environment variables."""
        self.config_file: str = config_file
        # Load .env if it exists (for local development only)
        if os.path.exists(config_file):
            try:
                from dotenv import load_dotenv
                load_dotenv(config_file)
                logger.info(f"Configuration loaded from {config_file}")
            except ImportError:
                logger.warning("python-dotenv not available, using environment variables only")

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Safely retrieve configuration value from environment."""
        value: Optional[str] = os.getenv(key, default)
        # Security: log access to sensitive keys (without exposing values)
        if key.upper().endswith("_KEY") or key.upper().endswith("_TOKEN"):
            logger.debug(f"Accessing credential key: {key}")
        return value

    def get_int(self, key: str, default: int = 0) -> int:
        """Retrieve integer configuration value."""
        value: Optional[str] = self.get(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            logger.warning(f"Invalid integer config: {key}={value}, using default={default}")
            return default

    def get_bool(self, key: str, default: bool = False) -> bool:
        """Retrieve boolean configuration value."""
        value: Optional[str] = self.get(key, "").lower()
        if value in ("true", "1", "yes", "on"):
            return True
        if value in ("false", "0", "no", "off"):
            return False
        return default
