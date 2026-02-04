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
        # Basic checks before resolution
        if len(user_path) > 1000:
            raise SecurityError(f"Path too long: {len(user_path)}")

        if '\\' in user_path:
            raise SecurityError(f"Windows-style separators not allowed: {user_path}")

        if user_path.startswith('/') or user_path.startswith('C:'):
             raise SecurityError(f"Absolute paths not allowed: {user_path}")

        # Resolve the path
        try:
            target_path = (self.repo_path / user_path).resolve()
            # Ensure the resolved path is within the repository
            if not self.repo_path.is_relative_to(target_path):
                raise SecurityError(f"Path traversal detected: {user_path}")
        except Exception as e:
            raise SecurityError(f"Invalid path: {user_path}") from e

        return target_path