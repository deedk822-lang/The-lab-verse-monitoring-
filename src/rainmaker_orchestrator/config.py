import os
from typing import Dict, List

 feature/elite-ci-cd-pipeline-1070897568806221897


 main
class ConfigManager:
    """Manages API keys and configuration"""

    def __init__(self, config_file: str = ".env"):
        self.config_file = config_file
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, str]:
        """Load configuration from environment or .env file"""
        config = {}

        # Try to load from .env file
        if os.path.exists(self.config_file):
 feature/elite-ci-cd-pipeline-1070897568806221897
            with open(self.config_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip().strip('"\'')

        # Override with environment variables
        config.update({
            'KIMI_API_KEY': os.getenv('KIMI_API_KEY'),
            'KIMI_API_BASE': os.getenv('KIMI_API_BASE', 'https://api.moonshot.ai/v1'),
            'OLLAMA_API_BASE': os.getenv('OLLAMA_API_BASE', 'http://localhost:11434/api'),
        })

            with open(self.config_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        config[key.strip()] = value.strip().strip("\"'")

        # Override with environment variables
        config.update(
            {
                "KIMI_API_KEY": os.getenv("KIMI_API_KEY"),
                "KIMI_API_BASE": os.getenv(
                    "KIMI_API_BASE", "https://api.moonshot.ai/v1"
                ),
                "OLLAMA_API_BASE": os.getenv(
                    "OLLAMA_API_BASE", "http://localhost:11434/api"
                ),
            }
        )
 main

        # Filter out None values so we can use .get() with defaults
        return {k: v for k, v in config.items() if v is not None}

 feature/elite-ci-cd-pipeline-1070897568806221897
    def get(self, key: str, default: str = '') -> str:

    def get(self, key: str, default: str = "") -> str:
 main
        """Get configuration value"""
        return self.config.get(key, default)

    def validate(self, required_keys: List[str]) -> List[str]:
        """Validate that required keys are present"""
        missing = [key for key in required_keys if not self.config.get(key)]
        return missing
