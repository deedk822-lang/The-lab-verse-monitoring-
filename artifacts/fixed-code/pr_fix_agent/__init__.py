"""
PR Fix Agent Core Library
Production-ready components for error analysis, security validation, and automated fixing
"""

from .analyzer import PRErrorAnalyzer, PRErrorFixer
from .models import ModelSelector, ModelSpec
from .observability import BudgetExceededError, CostTracker, LLMCost
from .ollama_agent import OllamaAgent, OllamaQueryError
from .orchestrator import CodeReviewOrchestrator
from .security import InputValidator, RateLimiter, SecurityError, SecurityValidator

__all__ = [
    # Security
    'SecurityError',
    'SecurityValidator',
    'InputValidator',
    'RateLimiter',
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

__version__ = '0.1.0'
__author__ = 'PR Fix Agent Team'

# Example usage of the classes

def analyze_error(error):
    """Analyze a potential error and return an analysis result."""
    analyzer = PRErrorAnalyzer()
    analysis_result = analyzer.analyze(error)
    return analysis_result

def fix_error(error):
    """Fix a potential error by applying appropriate changes."""
    fixer = PRErrorFixer()
    fixed_error = fixer.fix(error)
    return fixed_error