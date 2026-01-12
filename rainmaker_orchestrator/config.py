import os
 feat/complete-10268506225633119435
from dotenv import load_dotenv
from typing import List, Optional

class Settings:
    """
    Manages application configuration by loading from environment variables
    and .env files.
    """
    def __init__(self):
        # Load variables from .env file. Environment variables will override .env
        load_dotenv()

        # Set defaults and then override from environment
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
        self.workspace_path: str = os.getenv("WORKSPACE_PATH", "/workspace")
        self.environment: str = os.getenv("ENVIRONMENT", "production")

        # API configurations
        self.kimi_api_key: Optional[str] = os.getenv("KIMI_API_KEY")
        self.kimi_api_base: str = os.getenv("KIMI_API_BASE", "https://api.moonshot.ai/v1")
        self.ollama_api_base: str = os.getenv("OLLAMA_API_BASE", "http://localhost:11434/api")

    def validate(self, required_keys: List[str]) -> List[str]:
        """Validate that required keys are present"""
        missing = [key for key in required_keys if not getattr(self, key.lower(), None)]
        return missing

# Create a single, importable settings instance
settings = Settings()

from typing import Dict, List
from dotenv import load_dotenv

class ConfigManager:
    """Manages API keys and configuration"""

    def __init__(self, config_file: str = ".env"):
        load_dotenv(config_file)
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
        self.workspace_path: str = os.getenv("WORKSPACE_PATH", "./workspace")
        self.environment: str = os.getenv("ENVIRONMENT", "production")

        # API configurations
        self.kimi_api_key: str | None = os.getenv("KIMI_API_KEY")
        self.kimi_api_base: str = os.getenv("KIMI_API_BASE", "https://api.moonshot.ai/v1")
        self.ollama_api_base: str = os.getenv("OLLAMA_API_BASE", "http://localhost:11434/api")

    def get(self, key: str, default: str = '') -> str:
        """Get configuration value"""
        return getattr(self, key, default)

    def validate(self, required_keys: List[str]) -> List[str]:
        """Validate that required keys are present"""
        missing = [key for key in required_keys if not self.get(key)]
        return missing

settings = ConfigManager()
 feature/complete-orchestrator-and-scheduler-3340126171226885686
