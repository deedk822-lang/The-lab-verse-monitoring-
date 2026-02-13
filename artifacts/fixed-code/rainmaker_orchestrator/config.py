import logging
import os

logger: logging.Logger = logging.getLogger("config")

class ConfigManager:
    """Centralized configuration management with environment variable support."""

    def __init__(self, config_file: str = ".env") -> None:
        self.config_file: str = config_file
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Configuration file {config_file} does not exist")

        try:
            from dotenv import load_dotenv

            load_dotenv(config_file)
            logger.info("Configuration loaded from %s", config_file)
        except ImportError:
            logger.warning("python-dotenv not available, using environment variables only")

    def get(self, key: str, default: str | None = None) -> str | None:
        value: str | None = os.getenv(key, default)
        if key.upper().endswith("_KEY") or key.upper().endswith("_TOKEN"):
            logger.debug("Accessing credential key: %s", key)
        return value

    def get_int(self, key: str, default: int = 0) -> int:
        value: str | None = self.get(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            logger.warning("Invalid integer config: %s=%s, using default=%d", key, value, default)
            return default

    def get_bool(self, key: str, default: bool = False) -> bool:
        value: str = (self.get(key, "") or "").lower()
        if value in ("true", "1", "yes", "on"):
            return True
        if value in ("false", "0", "no", "off"):
            return False
        logger.warning("Invalid boolean config: %s=%s, using default=%s", key, value, default)
        return default