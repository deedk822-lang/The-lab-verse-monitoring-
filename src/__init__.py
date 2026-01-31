"""
PR Fix Agent Core Library
Production-ready components for error analysis and security validation
"""

from .analyzer import ErrorStatistics, PRErrorAnalyzer
from .security import InputValidator, RateLimiter, SecurityError, SecurityValidator

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

__version__ = '1.0.0'
__author__ = 'PR Fix Agent Team'

def create_security_error(error_message):
    return SecurityError(error_message)

def create_security_validator(config):
    return SecurityValidator(config)

def create_input_validator(config):
    return InputValidator(config)

def create_rate_limiter(config):
    return RateLimiter(config)

def create_perror_analyzer(config):
    return PRErrorAnalyzer(config)

def create_error_statistics(config):
    return ErrorStatistics(config)