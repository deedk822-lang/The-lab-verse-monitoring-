"""
Security sanitizers for prompt injection and input validation.
Implements defense-in-depth with multiple layers of protection.
"""

import re
import logging
from typing import Optional, List, Dict, Any
from html import escape
import unicodedata

logger = logging.getLogger(__name__)

# Dangerous patterns that could indicate prompt injection
INJECTION_PATTERNS = [
    r"ignore\s+(?:.*?\s+)?instructions?",
    r"disregard\s+(?:.*?\s+)?(?:previous|above|prior|instructions?)",
    r"forget\s+(?:everything|all|previous)",
    r"new\s+instructions?:",
    r"system\s*:\s*",
    r"<\|im_start\|>",
    r"<\|im_end\|>",
    r"\[INST\]",
    r"\[/INST\]",
    r"<s>|</s>",
    r"<<<.*>>>",
    r"PROMPT_START|PROMPT_END",
    r"jailbreak|DAN\s+mode",
]

# Compile patterns for efficiency
COMPILED_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in INJECTION_PATTERNS]

# Maximum safe lengths
MAX_PROMPT_LENGTH = 8000
MAX_CONTEXT_LENGTH = 32000


class PromptInjectionDetected(Exception):
    """Raised when potential prompt injection is detected."""
    pass


def normalize_unicode(text: str) -> str:
    """Normalize unicode to prevent obfuscation attacks."""
    if not text:
        return text

    # NFKC normalization to handle lookalike characters
    normalized = unicodedata.normalize('NFKC', text)

    # Remove zero-width and other invisible characters
    cleaned = ''.join(
        char for char in normalized
        if unicodedata.category(char) not in ('Cc', 'Cf', 'Cn', 'Co', 'Cs')
        or char in ('\n', '\r', '\t')
    )

    return cleaned


def detect_injection_patterns(text: str) -> List[str]:
    """
    Detect potential prompt injection patterns.
    Returns list of matched patterns.
    """
    matches = []
    normalized = normalize_unicode(text)

    for pattern in COMPILED_PATTERNS:
        if pattern.search(normalized):
            matches.append(pattern.pattern)

    return matches


def truncate_safely(text: str, max_length: int = MAX_PROMPT_LENGTH) -> str:
    """Truncate text to safe length, preserving word boundaries."""
    if len(text) <= max_length:
        return text

    truncated = text[:max_length]
    last_space = truncated.rfind(' ')

    if last_space > max_length * 0.8:  # If space is reasonably close
        return truncated[:last_space] + "..."

    return truncated + "..."


def sanitize_prompt(
    prompt: str,
    strict: bool = False,
    max_length: Optional[int] = None,
    allow_system_messages: bool = False
) -> str:
    """
    Sanitize user prompt to prevent injection attacks.

    Args:
        prompt: The user input to sanitize
        strict: If True, raise exception on detection; if False, clean and log
        max_length: Maximum allowed length (default: MAX_PROMPT_LENGTH)
        allow_system_messages: Whether to allow system-like formatting

    Returns:
        Sanitized prompt

    Raises:
        PromptInjectionDetected: If strict=True and injection detected
    """
    if not prompt:
        return ""

    max_length = max_length or MAX_PROMPT_LENGTH

    # Normalize unicode
    sanitized = normalize_unicode(prompt)

    # Check for injection patterns
    matched_patterns = detect_injection_patterns(sanitized)

    if matched_patterns:
        logger.warning(
            f"Potential prompt injection detected. Patterns: {matched_patterns}",
            extra={"prompt_preview": sanitized[:200]}
        )

        if strict:
            raise PromptInjectionDetected(
                f"Prompt contains suspicious patterns: {matched_patterns}"
            )

        # Remove matched patterns (soft mitigation)
        for pattern in COMPILED_PATTERNS:
            sanitized = pattern.sub('[FILTERED]', sanitized)

    # Remove system message markers if not allowed
    if not allow_system_messages:
        sanitized = re.sub(r'<\|.*?\|>', '', sanitized)
        sanitized = re.sub(r'\[/?INST\]', '', sanitized)
        sanitized = re.sub(r'</?s>', '', sanitized)

    # Truncate to safe length
    sanitized = truncate_safely(sanitized, max_length)

    # Strip excessive whitespace
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()

    return sanitized


def sanitize_context(
    context: Dict[str, Any],
    max_items: int = 50,
    max_context_length: int = MAX_CONTEXT_LENGTH
) -> Dict[str, Any]:
    """
    Sanitize context dictionary for LLM consumption.

    Args:
        context: Context dictionary
        max_items: Maximum number of context items
        max_context_length: Maximum total context length

    Returns:
        Sanitized context dictionary
    """
    if not context:
        return {}

    sanitized = {}
    total_length = 0
    item_count = 0

    for key, value in context.items():
        if item_count >= max_items:
            logger.warning(f"Context truncated at {max_items} items")
            break

        # Sanitize key
        safe_key = sanitize_prompt(str(key), max_length=100)

        # Sanitize value based on type
        if isinstance(value, str):
            safe_value = sanitize_prompt(value, max_length=2000)
        elif isinstance(value, (list, tuple)):
            safe_value = [
                sanitize_prompt(str(item), max_length=500)
                for item in list(value)[:20]  # Limit list size
            ]
        elif isinstance(value, dict):
            # Recursively sanitize nested dicts (one level only)
            safe_value = {
                sanitize_prompt(str(k), max_length=100):
                sanitize_prompt(str(v), max_length=500)
                for k, v in list(value.items())[:10]
            }
        else:
            safe_value = str(value)[:500]

        value_str = str(safe_value)
        if total_length + len(value_str) > max_context_length:
            logger.warning(f"Context truncated at {max_context_length} chars")
            break

        sanitized[safe_key] = safe_value
        total_length += len(value_str)
        item_count += 1

    return sanitized


def escape_html_entities(text: str) -> str:
    """Escape HTML entities to prevent XSS in web contexts."""
    return escape(text)


def sanitize_webhook_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize webhook payload for safe processing.

    Args:
        payload: Raw webhook payload

    Returns:
        Sanitized payload
    """
    def _sanitize_value(value: Any, depth: int = 0) -> Any:
        if depth > 5:  # Prevent deep recursion
            return str(value)[:100]

        if isinstance(value, str):
            return sanitize_prompt(value, max_length=5000)
        elif isinstance(value, dict):
            return {
                str(k)[:100]: _sanitize_value(v, depth + 1)
                for k, v in list(value.items())[:50]
            }
        elif isinstance(value, (list, tuple)):
            return [_sanitize_value(item, depth + 1) for item in list(value)[:50]]
        elif isinstance(value, (int, float, bool, type(None))):
            return value
        else:
            return str(value)[:500]

    return _sanitize_value(payload)


# Rate limiting helpers
class RateLimiter:
    """Simple in-memory rate limiter for additional protection."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: Dict[str, List[float]] = {}

    def is_allowed(self, key: str, current_time: float) -> bool:
        """Check if request is allowed under rate limit."""
        if key not in self._requests:
            self._requests[key] = []

        # Clean old requests
        cutoff = current_time - self.window_seconds
        self._requests[key] = [
            ts for ts in self._requests[key] if ts > cutoff
        ]

        # Check limit
        if len(self._requests[key]) >= self.max_requests:
            return False

        self._requests[key].append(current_time)
        return True
