import os
from dotenv import load_dotenv

class Settings:
    """
    Manages application configuration by loading from environment variables
    and .env files.
    """
    def __init__(self):
        # Load variables from .env file. Environment variables will override .env
        """
        Initialize Settings by loading .env and populating configuration attributes from environment variables.
        
        Calls load_dotenv() so values from a .env file are available, with explicit environment variables taking precedence. Initializes the following attributes (defaults shown when the environment variable is absent):
        - log_level: logging level, default "INFO"
        - workspace_path: path to workspace, default "/workspace"
        - environment: deployment environment, default "production"
        - kimi_api_key: Kimi API key, default None
        - kimi_api_base: base URL for the Kimi API, default "https://api.moonshot.ai/v1"
        - ollama_api_base: base URL for the Ollama API, default "http://localhost:11434/api"
        """
        load_dotenv()

        # Set defaults and then override from environment
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
        self.workspace_path: str = os.getenv("WORKSPACE_PATH", "/workspace")
        self.environment: str = os.getenv("ENVIRONMENT", "production")

        # API configurations
        self.kimi_api_key: str | None = os.getenv("KIMI_API_KEY")
        self.kimi_api_base: str = os.getenv("KIMI_API_BASE", "https://api.moonshot.ai/v1")
        self.ollama_api_base: str = os.getenv("OLLAMA_API_BASE", "http://localhost:11434/api")

# Create a single, importable settings instance
settings = Settings()