"""
PR Fix Agent Core Library
Production-ready components for error analysis and security validation
"""

# Import specific items from analyzer module
from .analyzer import ErrorStatistics, PRErrorAnalyzer

# Import specific items from security module
from .security import InputValidator, RateLimiter, SecurityError, SecurityValidator

# Define the list of all public items
__all__ = [
    # Security
    'SecurityError',
    'SecurityValidator',
    'InputValidator',
    'RateLimiter',
    # Analysis
    'PRErrorAnalyzer',
    'ErrorStatistics',
]

# Define the version and author information
__version__ = "1.0.0"
__author__ = "PR Fix Agent Team"

def import_required_modules():
    try:
        from .analyzer import ErrorStatistics, PRErrorAnalyzer
        from .security import InputValidator, RateLimiter, SecurityError, SecurityValidator
        return True
    except ModuleNotFoundError:
        print("Required modules not found. Please install them first.")
        return False

if import_required_modules():
    print(f"Successfully imported required modules.")
else:
    print("Failed to import required modules.")