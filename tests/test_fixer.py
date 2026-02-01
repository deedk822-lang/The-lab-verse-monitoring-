"""
Fixed Test File - No Duplication
Issue Fixed: 82 lines of duplicate production code removed
"""

<<<<<<< HEAD
import pytest
from unittest.mock import Mock
from pathlib import Path

# ✅ FIX: Direct import, no fallback duplication
from pr_fix_agent.analyzer import PRErrorFixer
from pr_fix_agent.ollama_agent import OllamaAgent as MockOllamaAgent
=======
from pathlib import Path

import pytest

# ✅ FIX: Direct import, no fallback duplication
from pr_fix_agent.analyzer import PRErrorFixer
from pr_fix_agent.ollama_agent import MockOllamaAgent
>>>>>>> main


class TestPRErrorFixerReal:
    """
    Tests using production code directly

    FIXED: No more 82-line fallback implementation
    """

    @pytest.fixture
    def mock_agent(self):
        """Use MockOllamaAgent (no HTTP calls)"""
        agent = MockOllamaAgent(model="test")
        agent.set_response("Generate", "def hello():\n    pass")
        return agent

    @pytest.fixture
    def fixer(self, mock_agent, tmp_path):
        """Create fixer with mock agent"""
        from pr_fix_agent.security import SecurityValidator

        validator = SecurityValidator(tmp_path)
        return PRErrorFixer(
            agent=mock_agent,
            repo_path=str(tmp_path),
            validator=validator
        )

    def test_fix_missing_file_creates_file(self, fixer, tmp_path):
        """Test: Creates missing file"""
        error = 'Error: File "test.py" not found'

        result = fixer.fix_missing_file_error(error)

        assert result is not None
        assert Path(result).exists()
        assert "def hello():" in Path(result).read_text()

    def test_fix_blocks_path_traversal(self, fixer):
        """Test: Blocks path traversal"""
        error = 'Error: File "../../../etc/passwd" not found'

        result = fixer.fix_missing_file_error(error)

        assert result is None  # Blocked

    def test_fix_missing_dependency_adds_to_requirements(self, fixer, tmp_path):
        """Test: Adds missing dependency"""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("requests==2.28.0\n")

        error = "ImportError: No module named 'numpy'"

        result = fixer.fix_missing_dependency(error)

        assert result is not None
        assert "numpy" in req_file.read_text().lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
