class SecurityError(Exception):
    """Base class for security validation errors"""

    def __init__(self, message: str):
        super().__init__(message)
def sanitize_relative_path(user_path: str) -> Path:
    # Simplify path using os.path.normpath
    normalized_path = os.path.normpath(user_path)
    
    # Perform basic checks on the sanitized path
    if len(normalized_path) > 1000:
        raise SecurityError(f"Path too long: {len(normalized_path)}")
    
    if "\\" in normalized_path:
        raise SecurityError(f"Windows-style separators not allowed: {normalized_path}")
    
    if normalized_path.startswith("/") or normalized_path.startswith("C:"):
        raise SecurityError(f"Absolute paths not allowed: {normalized_path}")
    
    return Path(normalized_path)
import re
from pathlib import Path

def validate_module_name(module_name: str) -> str:
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
def validate_file_extension(filename: str) -> bool:
    allowed = [".py", ".txt", ".md", ".yml", ".yaml", ".json", ".toml", ".cfg", ".ini"]
    return any(filename.endswith(ext) for ext in allowed)
class RateLimiter:
    """Simple rate limiter for API calls"""

    def __init__(self, max_requests: int = 100, window_seconds: int = 3600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = []

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
import json
import re

class SecurityError(Exception):
    """Base class for security validation errors"""

    def __init__(self, message: str):
        super().__init__(message)

def sanitize_relative_path(user_path: str) -> Path:
    # Simplify path using os.path.normpath
    normalized_path = os.path.normpath(user_path)
    
    # Perform basic checks on the sanitized path
    if len(normalized_path) > 1000:
        raise SecurityError(f"Path too long: {len(normalized_path)}")
    
    if "\\" in normalized_path:
        raise SecurityError(f"Windows-style separators not allowed: {normalized_path}")
    
    if normalized_path.startswith("/") or normalized_path.startswith("C:"):
        raise SecurityError(f"Absolute paths not allowed: {normalized_path}")
    
    return Path(normalized_path)

def validate_module_name(module_name: str) -> str:
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

def validate_file_extension(filename: str) -> bool:
    allowed = [".py", ".txt", ".md", ".yml", ".yaml", ".json", ".toml", ".cfg", ".ini"]
    return any(filename.endswith(ext) for ext in allowed)

class RateLimiter:
    """Simple rate limiter for API calls"""

    def __init__(self, max_requests: int = 100, window_seconds: int = 3600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = []

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