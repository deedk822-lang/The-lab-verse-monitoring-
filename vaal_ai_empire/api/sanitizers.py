"""
Input sanitization utilities for security.
Prevents prompt injection and other security issues.
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Dangerous patterns to detect/block
DANGEROUS_PATTERNS = [
    re.compile(r"(?i)(ignore|forget|disregard)\s+(previous|above|all)\s+(instructions|prompts|rules)"),
    re.compile(r"(?i)system\s*:\s*you\s+are"),
    re.compile(r"(?i)new\s+(instructions|rules|prompt)"),
    re.compile(r"(?i)(execute|run|eval)\s*\("),
    re.compile(r"<\s*script\s*>"),
    re.compile(r"javascript\s*:"),
]


def sanitize_prompt(prompt: str, max_length: int = 10000) -> str:
    """
    Sanitize user prompts to prevent injection attacks.
    
    Args:
        prompt: User input prompt
        max_length: Maximum allowed length
        
    Returns:
        Sanitized prompt
        
    Raises:
        ValueError: If prompt contains dangerous patterns
    """
    if not prompt:
        return ""
    
    # Truncate to max length
    if len(prompt) > max_length:
        logger.warning(f"Prompt truncated from {len(prompt)} to {max_length} chars")
        prompt = prompt[:max_length]
    
    # Check for dangerous patterns
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, prompt):
            logger.error(f"Dangerous pattern detected: {pattern}")
            raise ValueError("Prompt contains potentially unsafe content")
    
    # Remove null bytes
    prompt = prompt.replace('\x00', '')
    
    # Normalize whitespace
    prompt = re.sub(r'\s+', ' ', prompt).strip()
    
    return prompt


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filenames to prevent directory traversal.
    
    Args:
        filename: Input filename
        
    Returns:
        Sanitized filename
    """
    # Remove path separators
    filename = filename.replace('/', '').replace('\\', '')
    
    # Remove dangerous characters
    filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename)
    
    # Remove leading dots
    filename = filename.lstrip('.')
    
    return filename[:255]  # Max filename length
