import logging
import os
from typing import Optional

logger: logging.Logger = logging.getLogger("config")

class ConfigManager:
    """Centralized configuration management with environment variable support."""

    def __init__(self, config_file: str | None = None) -> None:
        self.config_file: str | None = config_file
        from pathlib import Path
        if Path(config_file).exists():
            try:
                logger.info("Configuration loaded from %s", config_file)
            except ImportError:
                logger.warning("python-dotenv not available, using environment variables only")

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        value: Optional[str] = os.getenv(key, default)
        if key.upper().endswith("_KEY") or key.upper().endswith("_TOKEN"):
            logger.debug("Accessing credential key: %s", key)
        return value

    def get_int(self, key: str, default: int = 0) -> int:
        value: Optional[str] = self.get(key)
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
        return default

# Example usage
config_manager = ConfigManager()
api_key = config_manager.get("API_KEY")
if api_key:
    print(f"API Key: {api_key}")
else:
    print("API Key not configured.")