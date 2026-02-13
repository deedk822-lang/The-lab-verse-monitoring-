"""
PR Fix Agent Core Library
Production-ready components for error analysis and security validation
"""

# Whitelist of allowed packages in 'analyzer' and 'security'
WHITELISTED_PACKAGES = {
    "analyzer": ["ErrorStatistics", "PRErrorAnalyzer"],
    "security": ["InputValidator", "RateLimiter", "SecurityError", "SecurityValidator"]
}

from . import analyzer, security

def check_package_whitelist(package_name):
    if package_name in WHITELISTED_PACKAGES:
        return True
    return False

try:
    if check_package_whitelist(analyzer.__name__):
        from .analyzer import ErrorStatistics, PRErrorAnalyzer
    else:
        raise ValueError(f"Package {analyzer.__name__} is not allowed. Please use a whitelisted package.")
except ImportError:
    print("Error importing packages. Check your setup.")

try:
    if check_package_whitelist(security.__name__):
        from .security import InputValidator, RateLimiter, SecurityError, SecurityValidator
    else:
        raise ValueError(f"Package {security.__name__} is not allowed. Please use a whitelisted package.")
except ImportError:
    print("Error importing packages. Check your setup.")

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

__version__ = "1.0.0"
__author__ = "PR Fix Agent Team"