import os
from typing import Dict, List

class ConfigManager:
    \"\"\"Manages API keys and configuration\"\"\"

    def __init__(self, config_file: str = \".env\"):
        self.config_file = config_file
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, str]:
        \"\"\"Load configuration from environment or .env file\"\"\"
        config = {}

        # Try to load from .env file
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip().strip('\"\'')

        # Override with environment variables
        config.update({
            'KIMI_API_KEY': os.getenv('KIMI_API_KEY'),
            'KIMI_API_BASE': os.getenv('KIMI_API_BASE', 'https://api.moonshot.ai/v1'),
            'OLLAMA_API_BASE': os.getenv('OLLAMA_API_BASE', 'http://localhost:11434/api'),
            'MISTRAL_API_KEY': os.getenv('MISTRAL_API_KEY'),
            'MISTRAL_API_BASE': os.getenv('MISTRAL_API_BASE', 'https://api.mistral.ai/v1'),
            'ZAI_API_KEY': os.getenv('ZAI_API_KEY') or os.getenv('zai-api-key'),
            'ZAI_API_BASE': os.getenv('ZAI_API_BASE', 'https://api.z.ai/api/paas/v4'),
            'HUBSPOT_ACCESS_TOKEN': os.getenv('HUBSPOT_ACCESS_TOKEN'),
        })

        # Filter out None values
        return {k: v for k, v in config.items() if v is not None}

    def get(self, key: str, default: str = \"\") -> str:
        \"\"\"Get configuration value\"\"\"
        return self.config.get(key, default)

    def validate(self, required_keys: List[str]) -> List[str]:
        \"\"\"Validate that required keys are present\"\"\"
        missing = [key for key in required_keys if not self.config.get(key)]
        return missing
