"""
Input sanitization utilities for security.
Prevents prompt injection and other security issues.
"""

import re
import logging
import unicodedata
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)

class PromptInjectionDetected(Exception):
    """Raised when prompt injection is detected in strict mode."""
    pass

# Dangerous patterns to detect/block
DANGEROUS_PATTERNS = [
    r"(?i)(ignore|forget|disregard)\s+(?:.*?\s+)?(instructions|prompts|rules|everything|above|all)",
    r"(?i)system\s*:\s*you\s+are",
    r"(?i)new\s+(instructions|rules|prompt)",
    r"(?i)(execute|run|eval)\s*\(",
    r"<\s*script\s*>",
    r"javascript\s*:",
    r"<\|im_start\|>",
    r"\[INST\]",
]

def detect_injection_patterns(text: str) -> List[str]:
    """Detect injection patterns in text."""
    matches = []
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, text):
            matches.append(pattern)
    return matches

def normalize_unicode(text: str) -> str:
    """Normalize unicode to prevent obfuscation."""
    return unicodedata.normalize('NFKC', text)

def sanitize_prompt(prompt: str, max_length: int = 10000, strict: bool = False, allow_system_messages: bool = True) -> str:
    """
    Sanitize user prompts to prevent injection attacks.
    """
    if not prompt:
        return ""
    
    # Normalize unicode
    prompt = normalize_unicode(prompt)

    # Truncate to max length
    if len(prompt) > max_length:
        logger.warning(f"Prompt truncated from {len(prompt)} to {max_length} chars")
        prompt = prompt[:max_length] + "..."

    # Check for dangerous patterns
    matches = detect_injection_patterns(prompt)
    if matches:
        logger.error(f"Dangerous patterns detected: {matches}")
        if strict:
            raise PromptInjectionDetected(f"Prompt contains potentially unsafe content")

        # Soft mode: filter patterns
        for pattern in matches:
            # Avoid infinite loop if replacement also matches
            prompt = re.sub(pattern, "[FILTERED]", prompt)

    if not allow_system_messages:
        prompt = prompt.replace("<|im_start|>", "").replace("<|im_end|>", "")
    
    # Remove null bytes
    prompt = prompt.replace('\x00', '')
    
    # Normalize whitespace
    prompt = re.sub(r'\s+', ' ', prompt).strip()
    
    return prompt

def sanitize_context(context: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize all strings in a context dictionary."""
    sanitized = {}
    for k, v in context.items():
        if isinstance(v, str):
            sanitized[k] = sanitize_prompt(v)
        elif isinstance(v, dict):
            sanitized[k] = sanitize_context(v)
        else:
            sanitized[k] = v
    return sanitized

def sanitize_webhook_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize webhook payload."""
    return sanitize_context(payload)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filenames to prevent directory traversal.
    """
    # Remove path separators
    filename = filename.replace('/', '').replace('\\', '')
    
    # Remove dangerous characters
    filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename)
    
    # Remove leading dots
    filename = filename.lstrip('.')
    
    return filename[:255]  # Max filename length

class RateLimiter:
    """Simple rate limiter placeholder."""
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
