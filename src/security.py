"""
Core Security and Validation Components
Proper library structure for reusable components
"""

import re
from pathlib import Path
from typing import List


class SecurityError(Exception):
    """Security validation error"""

    pass


class SecurityValidator:
    """Production-ready security validator"""

    def __init__(self, repo_path: Path):
        self.repo_path = Path(repo_path).resolve()

    def validate_path(self, user_path: str) -> Path:
        """
        Validate and sanitize file paths

        Args:
            user_path: User-provided path

        Returns:
            Validated absolute path

        Raises:
            SecurityError: If path is invalid or attempts traversal
        """
        # Security: Basic checks before resolution
        if len(user_path) > 1000:
            raise SecurityError(f"Path too long: {len(user_path)}")

        if "\\" in user_path:
            raise SecurityError(f"Windows-style separators not allowed: {user_path}")

        if user_path.startswith("/") or user_path.startswith("C:"):
            raise SecurityError(f"Absolute paths not allowed: {user_path}")

        # Resolve the path
        try:
            target_path = (self.repo_path / user_path).resolve()
        except Exception as e:
            raise SecurityError(f"Invalid path: {user_path}") from e

        # Check if it's within repo
        try:
            target_path.relative_to(self.repo_path)
        except ValueError:
            raise SecurityError(f"Path traversal detected: {user_path}")

        return target_path

    def validate_module_name(self, module_name: str) -> str:
        """
        Validate Python module names

        Args:
            module_name: Module name to validate

        Returns:
            Validated module name

        Raises:
            SecurityError: If module name is invalid or dangerous
        """
        # Check for shell metacharacters
        dangerous_chars = [";", "&", "|", "$", "`", "(", ")", "<", ">", "\n", "\r", "\x00"]
        if any(char in module_name for char in dangerous_chars):
            raise SecurityError(f"Dangerous characters in module name: {module_name}")

        # Check length (DoS prevention)
        if len(module_name) > 100:
            raise SecurityError(f"Module name too long: {len(module_name)} chars")

        # Validate format (alphanumeric, dash, underscore, dot)
        if not re.match(r"^[a-zA-Z0-9_\-\.]+$", module_name):
            raise SecurityError(f"Invalid module name format: {module_name}")

        return module_name

    def validate_file_extension(self, filename: str) -> bool:
        """
        Check if file extension is allowed

        Args:
            filename: Filename to check

        Returns:
            True if extension is allowed
        """
        allowed = [".py", ".txt", ".md", ".yml", ".yaml", ".json", ".toml", ".cfg", ".ini"]
        return any(filename.endswith(ext) for ext in allowed)

    def sanitize_input(self, user_input: str, max_length: int = 1000) -> str:
        """
        Sanitize user input

        Args:
            user_input: Input to sanitize
            max_length: Maximum allowed length

        Returns:
            Sanitized input

        Raises:
            SecurityError: If input is too long or contains dangerous content
        """
        if len(user_input) > max_length:
            raise SecurityError(f"Input too long: {len(user_input)} > {max_length}")

        # Remove null bytes
        if "\x00" in user_input:
            raise SecurityError("Null byte in input")

        return user_input.strip()


class InputValidator:
    """Additional input validation utilities"""

    @staticmethod
    def validate_json(data: str) -> bool:
        """Validate JSON structure"""
        import json

        try:
            json.loads(data)
            return True
        except Exception:
            return False

    @staticmethod
    def validate_yaml_safe(data: str) -> bool:
        """Validate YAML is safe to parse"""
        # Check for dangerous YAML constructs
        dangerous_patterns = [
            r"!!python/",
            r"__import__",
            r"eval\s*\(",
            r"exec\s*\(",
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, data):
                return False

        return True

    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format"""
        url_pattern = r"^https?://[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}(/.*)?$"
        return bool(re.match(url_pattern, url))


class RateLimiter:
    """Simple rate limiter for API calls"""

    def __init__(self, max_requests: int = 100, window_seconds: int = 3600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: List[float] = []

    def check_rate_limit(self) -> bool:
        """
        Check if rate limit is exceeded

        Returns:
            True if request is allowed
        """
        import time

        now = time.time()

        # Remove old requests outside window
        self.requests = [req for req in self.requests if now - req < self.window_seconds]

        # Check limit
        if len(self.requests) >= self.max_requests:
            return False

        # Record this request
        self.requests.append(now)
        return True
