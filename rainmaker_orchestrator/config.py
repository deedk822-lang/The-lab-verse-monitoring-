import logging
import os
from typing import Optional

logger: logging.Logger = logging.getLogger("config")


class ConfigManager:
    """Centralized configuration management with environment variable support."""

    def __init__(self, config_file: str = ".env") -> None:
        """
        Initialize the ConfigManager and optionally load variables from a .env file.
        
        If the specified file exists, attempt to load it using python-dotenv and log the outcome.
        The provided path is stored on the instance as `self.config_file`.
        
        Parameters:
            config_file (str): Path to a dotenv file to load environment variables from (default ".env").
        """
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
        """
        Retrieve a configuration value from the environment by key.
        
        Parameters:
            key (str): Environment variable name to read.
            default (Optional[str]): Value to return if the environment variable is not set.
        
        Returns:
            Optional[str]: The environment variable value if present, otherwise `default`.
        
        Notes:
            Access to keys ending with `_KEY` or `_TOKEN` triggers a debug log entry that records the key name without exposing its value.
        """
        value: Optional[str] = os.getenv(key, default)
        # Security: log access to sensitive keys (without exposing values)
        if key.upper().endswith("_KEY") or key.upper().endswith("_TOKEN"):
            logger.debug(f"Accessing credential key: {key}")
        return value

    def get_int(self, key: str, default: int = 0) -> int:
        """
        Return the integer value for a configuration key, falling back to the provided default when the key is missing or cannot be parsed.
        
        Parameters:
            key (str): Environment variable name to read.
            default (int): Value to return if the environment value is missing or not a valid integer.
        
        Returns:
            int: Parsed integer value for the key, or `default` if unset or unparsable.
        """
        value: Optional[str] = self.get(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            logger.warning(f"Invalid integer config: {key}={value}, using default={default}")
            return default

    def get_bool(self, key: str, default: bool = False) -> bool:
        """
        Parse a configuration value as a boolean.
        
        Recognizes the case-insensitive values "true", "1", "yes", "on" as truthy and
        "false", "0", "no", "off" as falsy. If the environment variable is not set or
        its value is not recognized, returns the provided default.
        
        Parameters:
            key (str): The configuration key or environment variable name to read.
            default (bool): Value to return when the config value is missing or unrecognized.
        
        Returns:
            `true` if the config value represents a truthy value, `false` otherwise.
        """
        raw_value = self.get(key, "")
        value = (raw_value or "").lower()
        if value in ("true", "1", "yes", "on"):
            return True
        if value in ("false", "0", "no", "off"):
            return False
        return default
