"""
PR Fix Agent Core Library for Error Analysis, Security Validation, and Automated Fixing
"""

from .analyzer import PRErrorAnalyzer, PRErrorFixer
from .models import ModelSelector, ModelSpec
from .observability import BudgetExceededError, CostTracker, LLMCost
from .ollama_agent import OllamaAgent, OllamaQueryError
from .orchestrator import CodeReviewOrchestrator
from .security import InputValidator, RateLimiter, SecurityError, SecurityValidator

__all__ = [
    # Security
    "InputValidator",
    "RateLimiter",
    # Analysis & Fixing
    'PRErrorAnalyzer',
    'PRErrorFixer',
    'OllamaAgent',
    'OllamaQueryError',
    # Observability
    'CostTracker',
    'LLMCost',
    'BudgetExceededError',
    # Models
    'ModelSpec',
    'ModelSelector',
    # Orchestration
    'CodeReviewOrchestrator',
]

__version__ = "0.1.0"
__author__ = "PR Fix Agent Team"

def check_package_name():
    """
    Check if the package name is appropriate and provides context.
    """
    print("Package Name: PR Fix Agent Core Library")
    print("Purpose: Provides tools for error analysis, security validation, and automated fixing.")
    print("Contact: prfixagent@example.com")

check_package_name()