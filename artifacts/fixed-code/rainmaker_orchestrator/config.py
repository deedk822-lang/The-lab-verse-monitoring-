import logging
import os

# Create a logger instance for ConfigManager
logger = logging.getLogger("config_manager")

class ConfigManager:
    """Centralized configuration management with environment variable support."""

    def __init__(self, config_file: str = ".env") -> None:
        self.config_file: str = config_file
        if os.path.exists(config_file):
            logger.info(f"Configuration loaded from {config_file}")
        else:
            logger.warning(f"No configuration file found at {config_file}")

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        value = os.getenv(key, default)
        if key.upper().endswith("_KEY") or key.upper().endswith("_TOKEN"):
            logger.debug("Accessing credential key: %s", key)
        return value

    def get_int(self, key: str, default: int = 0) -> int:
        value = os.getenv(key, "").strip()
        if not value:
            logger.warning(f"Invalid integer config: {key}={value}, using default={default}")
            return default
        try:
            return int(value)
        except ValueError:
            logger.error(f"Failed to convert {key}={value} to integer. Using default={default}")
            return default

    def get_bool(self, key: str, default: bool = False) -> bool:
        value = os.getenv(key, "").strip().lower()
        if value in ("true", "1", "yes", "on"):
            return True
        elif value in ("false", "0", "no", "off"):
            return False
        else:
            logger.error(f"Invalid boolean config: {key}={value}, using default={default}")
            return default