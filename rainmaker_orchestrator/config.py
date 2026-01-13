import os
from typing import Dict, List
from dotenv import load_dotenv

class ConfigManager:
    """Manages API keys and configuration"""

    def __init__(self, config_file: str = ".env"):
        """
        Initialize configuration by loading environment variables from the given file and populating instance attributes.
        
        Parameters:
            config_file (str): Path to a dotenv file to load environment variables from. Defaults to ".env".
        
        Attributes:
            log_level (str): Logging level; defaults to "INFO".
            workspace_path (str): Path to the workspace directory; defaults to "./workspace".
            environment (str): Deployment environment name; defaults to "production".
            kimi_api_key (str | None): API key for KIMI; None if not set.
            kimi_api_base (str): Base URL for the KIMI API; defaults to "https://api.moonshot.ai/v1".
            ollama_api_base (str): Base URL for the Ollama API; defaults to "http://localhost:11434/api".
        """
        load_dotenv(config_file)
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
        self.workspace_path: str = os.getenv("WORKSPACE_PATH", "./workspace")
        self.environment: str = os.getenv("ENVIRONMENT", "production")

        # API configurations
        self.kimi_api_key: str | None = os.getenv("KIMI_API_KEY")
        self.kimi_api_base: str = os.getenv("KIMI_API_BASE", "https://api.moonshot.ai/v1")
        self.ollama_api_base: str = os.getenv("OLLAMA_API_BASE", "http://localhost:11434/api")

    def get(self, key: str, default: str = '') -> str:
        """
        Return the configuration attribute value for the given key.
        
        Parameters:
            key (str): Name of the configuration attribute to retrieve.
            default (str): Value to return if the attribute does not exist.
        
        Returns:
            str: The attribute's value if present, otherwise `default`.
        """
        return getattr(self, key, default)

    def validate(self, required_keys: List[str]) -> List[str]:
        """
        Return the list of required configuration keys that are missing or have falsy values.
        
        Parameters:
            required_keys (List[str]): Names of configuration attributes to check on this ConfigManager.
        
        Returns:
            List[str]: The subset of `required_keys` whose corresponding configuration values are missing or falsy.
        """
        missing = [key for key in required_keys if not self.get(key)]
        return missing

settings = ConfigManager()