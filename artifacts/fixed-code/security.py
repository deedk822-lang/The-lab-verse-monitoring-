import re
from pathlib import Path

class InputValidator:
    """Additional input validation utilities"""

    @staticmethod
    def validate_json(data: str) -> bool:
        """Validate JSON structure"""
        try:
            json.loads(data)
            return True
        except:
            return False

    @staticmethod
    def validate_yaml_safe(data: str) -> bool:
        """Validate YAML is safe to parse"""
        # Check for dangerous YAML constructs
        dangerous_patterns = [
            r'!!python/',
            r'__import__',
            r'eval\s*\(',
            r'exec\s*\(',
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, data):
                return False

        return True

    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format"""
        url_pattern = r'^https?://[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}(/.*)?$'
        return bool(re.match(url_pattern, url))

    @staticmethod
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

        # Remove null bytes and extra spaces
        cleaned_input = user_input.strip()

        # Check for shell metacharacters
        dangerous_chars = [';', '&', '|', '$', '`', '(', ')', '<', '>', '\n', '\r', '\x00']
        if any(char in cleaned_input for char in dangerous_chars):
            raise SecurityError("Dangerous characters in input")

        return cleaned_input

    @staticmethod
    def sanitize_path(user_path: str) -> Path:
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

        if '\\' in user_path:
            raise SecurityError(f"Windows-style separators not allowed: {user_path}")

        if user_path.startswith('/') or user_path.startswith('C:'):
             raise SecurityError(f"Absolute paths not allowed: {user_path}")

        # Resolve the path
        try:
            target_path = (Path(user_path).resolve())
        except Exception as e:
            raise SecurityError(f"Invalid path: {user_path}") from e

        # Check if it's within repo
        try:
            target_path.relative_to(Path(self.repo_path))
        except ValueError:
            raise SecurityError(f"Path traversal detected: {user_path}")

        return target_path

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Validate Python module names

        Args:
            filename: Module name to validate

        Returns:
            Validated module name

        Raises:
            SecurityError: If module name is invalid or dangerous
        """
        # Check for shell metacharacters
        dangerous_chars = [';', '&', '|', '$', '`', '(', ')', '<', '>', '\n', '\r', '\x00']
        if any(char in filename for char in dangerous_chars):
            raise SecurityError(f"Dangerous characters in module name: {filename}")

        # Check length (DoS prevention)
        if len(filename) > 100:
            raise SecurityError(f"Module name too long: {len(filename)} chars")

        # Validate format (alphanumeric, dash, underscore, dot)
        if not re.match(r'^[a-zA-Z0-9_\-\.]+$', filename):
            raise SecurityError(f"Invalid module name format: {filename}")

        return filename