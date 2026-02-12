"""Rainmaker Orchestrator - AI-powered task orchestration and self-healing."""

__version__ = "0.1.0"

# Define sensitive configuration parameters as environment variables instead of hard-coded values
import os

# Environment variable for the Rainmaker Orchestrator API key
API_KEY = os.getenv('RAINMAKER_API_KEY', 'your_api_key_here')

# Environment variable for the Rainmaker Orchestrator secret token
SECRET_TOKEN = os.getenv('RAINMAKER_SECRET_TOKEN', 'your_secret_token_here')

__all__ = [
    "RainmakerOrchestrator",
    "SelfHealingAgent",
    "ConfigManager",
]

from rainmaker_orchestrator.orchestrator import RainmakerOrchestrator
from rainmaker_orchestrator.agents.healer import SelfHealingAgent
from rainmaker_orchestrator.config import ConfigManager

# Use the environment variables in your code
if API_KEY:
    # Initialize Rainmaker Orchestrator with the API key and secret token
    orchestrator = RainmakerOrchestrator(api_key=API_KEY, secret_token=SECRET_TOKEN)

else:
    # Handle case where API key is not provided
    raise ValueError("Rainmaker Orchestrator requires an API key")

# Use the environment variables in your code
if SECRET_TOKEN:
    # Initialize SelfHealingAgent with the secret token
    healer = SelfHealingAgent(secret_token=SECRET_TOKEN)

else:
    # Handle case where secret token is not provided
    raise ValueError("Rainmaker Orchestrator requires a secret token")