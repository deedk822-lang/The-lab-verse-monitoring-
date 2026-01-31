"""
Input Validation & Rate Limiting - Global Production Standard (S7)
Prevents injection attacks and enforces usage limits.
"""

import re
from typing import Any, Dict, List, Optional, Set
from pathlib import Path

import structlog

logger = structlog.get_logger()


class SecurityError(Exception):
    """Security validation error"""
    pass


class SecurityValidator:
    """
    Validates inputs for security issues.

    Checks:
    - Path traversal attempts
    - Command injection
    - SQL injection patterns
    - Oversized inputs
    """

    # Patterns that indicate injection attacks
    SQLI_PATTERNS = [
        r"(\%27)|(\')|(\-\-)|(\%23)|(#)",
        r"((\%3D)|(=))[^\n]*((\%27)|(\')|(\-\-)|(\%3B)|(;))",
        r"\w*((\%27)|(\'))((\%6F)|o|(\%4F))((\%72)|r|(\%52))",
        r"((\%27)|(\'))union",
        r"exec(\s|\+)+(s|x)p\w+",
        r"UNION\s+SELECT",
        r"INSERT\s+INTO",
        r"DELETE\s+FROM",
        r"DROP\s+TABLE",
    ]

    CMD_INJECTION_PATTERNS = [
        r"[;&|`$]",
        r"\$\(",
        r"`.*`",
        r"\|\s*\w+",
    ]

    def __init__(
        self,
        max_input_size: int = 100_000,  # 100KB
        allowed_paths: Optional[Set[Path]] = None
    ):
        self.max_input_size = max_input_size
        self.allowed_paths = allowed_paths or set()
        self.sqli_patterns = [re.compile(p, re.IGNORECASE) for p in self.SQLI_PATTERNS]
        self.cmd_patterns = [re.compile(p, re.IGNORECASE) for p in self.CMD_INJECTION_PATTERNS]

    def validate_path(self, path: str, base_dir: Path) -> Path:
        """
        Validate path is within allowed base directory.

        Args:
            path: User-provided path
            base_dir: Base directory that paths must be within

        Returns:
            Resolved Path object

        Raises:
            SecurityError: If path traversal detected
        """
        try:
            # Resolve the path
            target = (base_dir / path).resolve()
            base_resolved = base_dir.resolve()

            # Check if the resolved path is within base_dir
            if not str(target).startswith(str(base_resolved)):
                logger.warning(
                    "path_traversal_detected",
                    path=path,
                    target=str(target),
                    base=str(base_resolved)
                )
                raise SecurityError(f"Path traversal detected: {path}")

            return target

        except Exception as e:
            if isinstance(e, SecurityError):
                raise
            logger.error("path_validation_error", path=path, error=str(e))
            raise SecurityError(f"Invalid path: {path}")

    def validate_input_size(self, data: str) -> None:
        """Check input size is within limits."""
        if len(data) > self.max_input_size:
            logger.warning(
                "input_too_large",
                size=len(data),
                max_size=self.max_input_size
            )
            raise SecurityError(f"Input exceeds maximum size of {self.max_input_size} bytes")

    def check_sql_injection(self, input_str: str) -> bool:
        """
        Check for potential SQL injection patterns.

        Returns:
            True if suspicious patterns found
        """
        for pattern in self.sqli_patterns:
            if pattern.search(input_str):
                logger.warning("potential_sqli_detected", input=input_str[:100])
                return True
        return False

    def check_command_injection(self, input_str: str) -> bool:
        """
        Check for potential command injection patterns.

        Returns:
            True if suspicious patterns found
        """
        for pattern in self.cmd_patterns:
            if pattern.search(input_str):
                logger.warning("potential_cmd_injection_detected", input=input_str[:100])
                return True
        return False

    def validate_code_input(self, code: str) -> None:
        """
        Validate code input for security issues.

        Raises:
            SecurityError: If validation fails
        """
        self.validate_input_size(code)

        # Check for dangerous patterns in code
        dangerous_imports = [
            r"import\s+os\s*",
            r"import\s+subprocess\s*",
            r"import\s+sys\s*",
            r"__import__\s*\(",
            r"eval\s*\(",
            r"exec\s*\(",
            r"compile\s*\(",
            r"open\s*\(",
            r"file\s*\(",
        ]

        for pattern in dangerous_imports:
            if re.search(pattern, code, re.IGNORECASE):
                logger.warning("dangerous_code_pattern", pattern=pattern, code=code[:100])
                raise SecurityError(f"Dangerous code pattern detected: {pattern}")


class InputValidator:
    """
    General input validation utilities.
    """

    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """
        Sanitize a string input.

        - Truncates to max_length
        - Removes control characters
        - Strips whitespace
        """
        # Remove control characters except newlines and tabs
        sanitized = "".join(
            char for char in value
            if char == '\n' or char == '\t' or (ord(char) >= 32 and ord(char) < 127)
        )
        return sanitized.strip()[:max_length]

    @staticmethod
    def validate_email(email: str) -> bool:
        """Basic email validation."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    @staticmethod
    def validate_uuid(uuid_str: str) -> bool:
        """Validate UUID format."""
        pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        return bool(re.match(pattern, uuid_str, re.IGNORECASE))


class RateLimiter:
    """
    Simple in-memory rate limiter.

    For production, use Redis-backed rate limiting.
    """

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # Store request timestamps per key
        self._requests: Dict[str, List[float]] = {}

    def is_allowed(self, key: str) -> bool:
        """
        Check if request is within rate limit.

        Args:
            key: Unique identifier (e.g., IP address, user ID)

        Returns:
            True if request is allowed
        """
        import time

        now = time.time()

        # Get or create request list for this key
        req_list: List[float] = self._requests.get(key, [])

        # Remove old requests outside the window
        req_list = [t for t in req_list if now - t < self.window_seconds]

        # Check if under limit
        if len(req_list) < self.max_requests:
            req_list.append(now)
            self._requests[key] = req_list
            return True

        self._requests[key] = req_list
        logger.warning("rate_limit_exceeded", key=key, count=len(req_list))
        return False

    def get_remaining(self, key: str) -> int:
        """Get remaining requests in current window."""
        import time

        now = time.time()
        req_list: List[float] = self._requests.get(key, [])
        req_list = [t for t in req_list if now - t < self.window_seconds]
        return max(0, self.max_requests - len(req_list))
