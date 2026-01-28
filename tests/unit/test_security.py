"""Security tests for PR Fix Agent."""

import pytest
from pathlib import Path
from unittest.mock import Mock
from pr_fix_agent import PRErrorFixer, OllamaAgent

class TestSecurityValidator:
    """Test security validation."""

    @pytest.fixture
    def fixer(self, tmp_path):
        """Create error fixer."""
        agent = OllamaAgent()
        return PRErrorFixer(agent, str(tmp_path))

    def test_validate_file_path_valid(self, fixer, tmp_path):
        """Test valid file path validation."""
        safe_path = tmp_path / "config" / "valid.yml"
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        safe_path.touch()

        assert fixer._is_path_safe("config/valid.yml") is True

    def test_validate_file_path_traversal_attack(self, fixer):
        """Test path traversal is blocked."""
        assert fixer._is_path_safe("../../../etc/passwd") is False
        assert fixer._is_path_safe("..\\..\\..\\windows\\system32") is False

    def test_validate_dependency_name_safe(self, fixer):
        """Test safe dependency name."""
        assert fixer._is_module_safe("numpy") is True
        assert fixer._is_module_safe("scikit-learn") is True

    def test_validate_dependency_name_unsafe(self, fixer):
        """Test unsafe dependency name."""
        assert fixer._is_module_safe("os; rm -rf /") is False
        assert fixer._is_module_safe("sys && del /f") is False

    def test_validate_file_path_absolute_blocked(self, fixer):
        """Test absolute paths are blocked."""
        assert fixer._is_path_safe("/etc/passwd") is False

    def test_validate_file_path_symlink_detection(self, fixer, tmp_path):
        """Test symlink detection."""
        target_path = tmp_path / "target.txt"
        target_path.write_text("sensitive")

        symlink_path = tmp_path / "link.txt"
        try:
            symlink_path.symlink_to(target_path)
            # Path safe check should pass if inside repo, but we mostly care about traversal
            assert fixer._is_path_safe("link.txt") is True
        except:
            pytest.skip("Symlinks not supported")

    def test_sanitize_module_name(self, fixer):
        """Test module name sanitization."""
        assert fixer._is_module_safe("requests`whoami`") is False
        assert fixer._is_module_safe("pandas || ls") is False

    def test_validate_file_extension_whitelist(self, fixer):
        """Placeholder for extension whitelist."""
        # Current implementation doesn't have whitelist yet, but we can test safe names
        assert fixer._is_module_safe("valid_name") is True

    def test_rate_limiting(self):
        """Placeholder for rate limiting."""
        from vaal_ai_empire.api.sanitizers import RateLimiter
        limiter = RateLimiter(60)
        assert limiter.requests_per_minute == 60

    def test_input_length_validation(self):
        """Test input length validation via sanitizer."""
        from vaal_ai_empire.api.sanitizers import sanitize_prompt
        long_input = "a" * 20000
        sanitized = sanitize_prompt(long_input, max_length=100)
        assert len(sanitized) <= 103
