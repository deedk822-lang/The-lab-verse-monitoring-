"""
Core Security and Validation Components
Proper library structure for reusable components
"""

import json
import re
import threading
from pathlib import Path


class SecurityError(Exception):
    """Security validation error"""


class SecurityValidator:
    """Production-ready security validator"""

    def __init__(self, repo_path: Path):
        self.repo_path = Path(repo_path).resolve()

    def validate_path(self, user_path: str) -> Path:
        """Validate and sanitize file paths."""
        try:
            target_path = (self.repo_path / user_path).resolve()
        except Exception as e:
            raise SecurityError(f"Invalid path: {user_path}") from e

        try:
            target_path.relative_to(self.repo_path)
        except ValueError as e:
            raise SecurityError(f"Path traversal detected: {user_path}") from e

        return target_path

    def validate_module_name(self, module_name: str) -> str:
        """Validate Python module names."""
        dangerous_chars = [";", "&", "|", "$", "`", "(", ")", "<", ">", "\n", "\r", "\x00"]
        if any(char in module_name for char in dangerous_chars):
            raise SecurityError(f"Dangerous characters in module name: {module_name}")

        if len(module_name) > 100:
            raise SecurityError(f"Module name too long: {len(module_name)} chars")

        if not re.match(r"^[a-zA-Z0-9_\-\.]+$", module_name):
            raise SecurityError(f"Invalid module name format: {module_name}")

        return module_name

    def validate_file_extension(self, filename: str) -> bool:
        """Check if file extension is allowed."""
        allowed = [".py", ".txt", ".md", ".yml", ".yaml", ".json", ".toml", ".cfg", ".ini"]
        return any(filename.endswith(ext) for ext in allowed)

    def sanitize_input(self, user_input: str, max_length: int = 1000) -> str:
        """Sanitize user input."""
        if len(user_input) > max_length:
            raise SecurityError(f"Input too long: {len(user_input)} > {max_length}")

        if "\x00" in user_input:
            raise SecurityError("Null byte in input")

        return user_input.strip()


class InputValidator:
    """Additional input validation utilities"""

    @staticmethod
    def validate_json(data: str) -> bool:
        """Validate JSON structure."""
        try:
            json.loads(data)
            return True
        except (json.JSONDecodeError, TypeError):
            return False

    @staticmethod
    def validate_yaml_safe(data: str) -> bool:
        """Validate YAML is safe to parse."""
        dangerous_patterns = [r"!!python/", r"__import__", r"eval\s*\(", r"exec\s*\("]

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
    """Simple rate limiter for API calls (thread-safe)."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 3600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = []
        self._lock = threading.Lock()

    def check_rate_limit(self) -> bool:
        """Check if rate limit is exceeded."""
        import time

        now = time.time()

        with self._lock:
            self.requests = [req for req in self.requests if now - req < self.window_seconds]

            if len(self.requests) >= self.max_requests:
                return False

            self.requests.append(now)

        return True
