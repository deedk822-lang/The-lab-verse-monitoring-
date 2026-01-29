"""Tests for error fixing functionality."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from pr_fix_agent import PRErrorFixer, OllamaAgent

class TestPRErrorFixer:
    """Test error fixer."""

    @pytest.fixture
    def fixer(self, tmp_path):
        """Create error fixer."""
        agent = OllamaAgent()
        return PRErrorFixer(agent, str(tmp_path))

    def test_fix_missing_file_success(self, fixer, tmp_path):
        """Test successful missing file fix."""
        with patch.object(OllamaAgent, 'query', return_value="print('hello')"):
            error = 'Error: "scripts/test.py" not found'
            result = fixer.fix_missing_file_error(error)

            assert "Created" in result
            assert (tmp_path / "scripts/test.py").exists()
            assert (tmp_path / "scripts/test.py").read_text() == "print('hello')"

    def test_fix_missing_file_no_match(self, fixer):
        """Test fix with no filename match."""
        error = "Error: Something else happened"
        result = fixer.fix_missing_file_error(error)
        assert result is None

    def test_fix_missing_file_security_blocked(self, fixer):
        """Test fix blocked by security validation."""
        error = 'Error: "../../../etc/passwd" not found'
        result = fixer.fix_missing_file_error(error)
        assert result is None

    def test_fix_broken_submodule_success(self, fixer):
        """Test successful submodule fix."""
        error = "fatal: No url found for submodule path 'Open-AutoGLM'"
        result = fixer.fix_broken_submodule(error)
        assert "Fixed" in result
        assert "Open-AutoGLM" in result

    def test_fix_missing_dependency_success(self, fixer, tmp_path):
        """Test successful dependency fix."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("requests")

        error = "ImportError: No module named 'numpy'"
        result = fixer.fix_missing_dependency(error)

        assert "Added" in result
        assert "numpy" in req_file.read_text()

    def test_fix_missing_dependency_no_match(self, fixer):
        """Test fix with no module match."""
        error = "Error: Something else"
        result = fixer.fix_missing_dependency(error)
        assert result is None

    def test_fix_missing_dependency_suspicious_name(self, fixer):
        """Test fix with suspicious module name."""
        error = "ImportError: No module named 'os; rm -rf /'"
        result = fixer.fix_missing_dependency(error)
        assert result is None
