"""REAL Tests for PRErrorFixer

CI/CD ready:
- No merge artifacts
- No sys.path hacks
- No fallback mock implementations shadowing production code

These tests validate file/submodule/dependency fix behaviors using a mock agent.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock

from pr_fix_agent.analyzer import PRErrorFixer


class MockOllamaAgent:
    """Deterministic mock agent."""

    def query(self, prompt, temperature=0.2):
        if "Generate code" in prompt:
            return (
                "```python\n"
                "def main():\n"
                "    return 0\n"
                "\n"
                "if __name__ == '__main__':\n"
                "    main()\n"
                "```"
            )
        return "# Generated code"


class TestPRErrorFixerReal:
    @pytest.fixture
    def temp_repo(self):
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def agent(self):
        return MockOllamaAgent()

    @pytest.fixture
    def fixer(self, agent, temp_repo):
        return PRErrorFixer(agent, str(temp_repo))

    def test_fix_missing_file_creates_file(self, fixer, temp_repo):
        error = 'Error: "scripts/test.py" not found'
        result = fixer.fix_missing_file_error(error)
        assert result is not None
        created = Path(result)
        assert created.exists()
        assert created.parent == temp_repo / "scripts"

    def test_fix_missing_file_rejects_path_traversal(self, fixer):
        for attack in [
            'Error: "../../../etc/passwd" not found',
            'Error: "../../etc/shadow" not found',
            'Error: "/etc/passwd" not found',
        ]:
            assert fixer.fix_missing_file_error(attack) is None

    def test_fix_submodule_removes_entry(self, fixer, temp_repo):
        gitmodules = temp_repo / ".gitmodules"
        gitmodules.write_text(
            """[submodule \"good\"]\n    path = good\n    url = https://example.com/good.git\n"
            "[submodule \"broken\"]\n    path = broken\n    url = https://example.com/broken.git\n"
            "[submodule \"other\"]\n    path = other\n    url = https://example.com/other.git\n"""
        )

        error = "fatal: No url found for submodule path 'broken'"
        result = fixer.fix_submodule_error(error)
        assert result is not None

        content = gitmodules.read_text()
        assert '[submodule "good"]' in content
        assert '[submodule "other"]' in content
        assert '[submodule "broken"]' not in content

    def test_fix_missing_dependency_adds_to_requirements(self, fixer, temp_repo):
        req_file = temp_repo / "requirements.txt"
        req_file.write_text("requests==2.28.0\nflask==2.0.1\n")

        error = "ImportError: No module named 'numpy'"
        result = fixer.fix_missing_dependency(error)
        assert result is not None

        content = req_file.read_text()
        assert "numpy" in content

    def test_fix_missing_dependency_doesnt_duplicate(self, fixer, temp_repo):
        req_file = temp_repo / "requirements.txt"
        req_file.write_text("numpy==1.21.0\nrequests==2.28.0\n")

        error = "ImportError: No module named 'numpy'"
        fixer.fix_missing_dependency(error)

        content = req_file.read_text()
        assert content.count("numpy") == 1

    def test_error_recovery_invalid_response(self, fixer):
        fixer.agent = Mock()
        fixer.agent.query = Mock(return_value="This is not code at all!")

        error = 'Error: "test.py" not found'
        # Should not crash
        fixer.fix_missing_file_error(error)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
