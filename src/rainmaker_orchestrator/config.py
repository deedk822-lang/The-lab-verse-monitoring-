import os
from typing import Dict, List, Optional

class ConfigManager:
    """Manages API keys and configuration"""

    def __init__(self, config_file: str = ".env") -> None:
        self.config_file = config_file
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, str]:
        """Load configuration from environment or .env file"""
        config: Dict[str, str] = {}

        # Try to load from .env file
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip().strip('"\'')

        # Override with environment variables
        env_vars: Dict[str, Optional[str]] = {
            'KIMI_API_KEY': os.getenv('KIMI_API_KEY'),
            'KIMI_API_BASE': os.getenv('KIMI_API_BASE', 'https://api.moonshot.ai/v1'),
            'OLLAMA_API_BASE': os.getenv('OLLAMA_API_BASE', 'http://localhost:11434/api'),
        } # type: ignore

        for key, value in env_vars.items():
            if value is not None:
                config[key] = value

        return config

    def get(self, key: str, default: str = '') -> str:
        """Get configuration value"""
        return self.config.get(key, default)

    def validate(self, required_keys: List[str]) -> List[str]:
        """Validate that required keys are present"""
        missing = [key for key in required_keys if not self.config.get(key)]
        return missing
