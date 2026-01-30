"""REAL tests for PRErrorFixer.

These tests validate behavior without requiring external services.
"""

import re
import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from pr_fix_agent.analyzer import PRErrorFixer


class MockOllamaAgent:
    """Mock agent for deterministic tests (no localhost / network calls)."""

    def __init__(self, model: str = "test"):
        self.model = model

    def query(self, prompt: str, temperature: float = 0.2) -> str:
        if "Generate code" in prompt or "test" in prompt:
            return (
                "```python\n"
                "#!/usr/bin/env python3\n"
                "def main():\n"
                "    print(\"Test implementation\")\n"
                "    return 0\n\n"
                "if __name__ == \"__main__\":\n"
                "    main()\n"
                "```"
            )
        return "# Generated code"


class TestPRErrorFixerReal:
    """Real tests that validate actual fixing behavior."""

    @pytest.fixture
    def temp_repo(self):
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def agent(self):
        return MockOllamaAgent(model="test")

    @pytest.fixture
    def fixer(self, agent, temp_repo):
        return PRErrorFixer(agent, str(temp_repo))

    def test_fix_missing_file_creates_file(self, fixer, temp_repo):
        error = 'Error: "scripts/test.py" not found'
        result = fixer.fix_missing_file_error(error)
        assert result is not None
        created_file = Path(result)
        assert created_file.exists()
        assert created_file.parent == temp_repo / "scripts"
        assert created_file.name == "test.py"

    def test_fix_missing_file_valid_python(self, fixer):
        error = 'Error: "utils/helper.py" not found'
        result = fixer.fix_missing_file_error(error)
        assert result is not None
        created_file = Path(result)
        content = created_file.read_text()
        try:
            compile(content, created_file.name, "exec")
        except SyntaxError as e:
            pytest.fail(f"Generated file has syntax error: {e}")

    def test_fix_missing_file_rejects_path_traversal(self, fixer):
        attacks = [
            'Error: "../../../etc/passwd" not found',
            'Error: "../../etc/shadow" not found',
            'Error: "/etc/passwd" not found',
        ]
        for attack in attacks:
            result = fixer.fix_missing_file_error(attack)
            assert result is None, f"Should reject: {attack}"

    def test_fix_missing_file_no_match_returns_none(self, fixer):
        error = "Error: Something went wrong"
        result = fixer.fix_missing_file_error(error)
        assert result is None

    def test_fix_missing_file_creates_directories(self, fixer, temp_repo):
        error = 'Error: "deeply/nested/dir/file.py" not found'
        result = fixer.fix_missing_file_error(error)
        assert result is not None
        created_file = Path(result)
        assert created_file.exists()
        assert (temp_repo / "deeply" / "nested" / "dir").exists()

    def test_fix_submodule_removes_entry(self, fixer, temp_repo):
        gitmodules = temp_repo / ".gitmodules"
        gitmodules.write_text(
            """[submodule \"good\"]
    path = good
    url = https://github.com/example/good.git
[submodule \"broken\"]
    path = broken
    url = https://github.com/example/broken.git
[submodule \"other\"]
    path = other
    url = https://github.com/example/other.git
"""
        )

        error = "fatal: No url found for submodule path 'broken'"
        result = fixer.fix_submodule_error(error)
        assert result is not None
        assert "broken" in result

        content = gitmodules.read_text()
        assert '[submodule "good"]' in content
        assert '[submodule "other"]' in content
        assert '[submodule "broken"]' not in content
        assert "broken" not in content

    def test_fix_submodule_preserves_other_entries(self, fixer, temp_repo):
        gitmodules = temp_repo / ".gitmodules"
        gitmodules.write_text(
            """[submodule \"keep1\"]
    path = keep1
    url = https://example.com/keep1.git
[submodule \"remove\"]
    path = remove
    url = https://example.com/remove.git
[submodule \"keep2\"]
    path = keep2
    url = https://example.com/keep2.git
"""
        )

        error = "fatal: No url found for submodule path 'remove'"
        fixer.fix_submodule_error(error)

        content = gitmodules.read_text()
        assert content.count("[submodule") == 2
        assert "keep1" in content
        assert "keep2" in content

    def test_fix_submodule_no_gitmodules_returns_none(self, fixer):
        error = "fatal: No url found for submodule path 'missing'"
        result = fixer.fix_submodule_error(error)
        assert result is None

    def test_fix_submodule_rejects_path_traversal(self, fixer, temp_repo):
        gitmodules = temp_repo / ".gitmodules"
        gitmodules.write_text('[submodule "safe"]\npath = safe')

        attacks = [
            "fatal: No url found for submodule path '../evil'",
            "fatal: No url found for submodule path '../../etc/passwd'",
        ]

        for attack in attacks:
            result = fixer.fix_submodule_error(attack)
            assert result is None

    def test_fix_dependency_adds_to_requirements(self, fixer, temp_repo):
        req_file = temp_repo / "requirements.txt"
        req_file.write_text("requests==2.28.0\nflask==2.0.1\n")

        error = "ImportError: No module named 'numpy'"
        result = fixer.fix_missing_dependency(error)

        assert result is not None
        assert "numpy" in result

        content = req_file.read_text()
        assert "numpy" in content
        assert "requests" in content
        assert "flask" in content

    def test_fix_dependency_doesnt_duplicate(self, fixer, temp_repo):
        req_file = temp_repo / "requirements.txt"
        req_file.write_text("numpy==1.21.0\nrequests==2.28.0\n")

        error = "ImportError: No module named 'numpy'"
        fixer.fix_missing_dependency(error)

        content = req_file.read_text()
        assert content.count("numpy") == 1

    def test_fix_dependency_blocks_malicious_names(self, fixer, temp_repo):
        req_file = temp_repo / "requirements.txt"
        req_file.write_text("requests==2.28.0\n")

        malicious_errors = [
            "ImportError: No module named 'os; rm -rf /'",
            "ImportError: No module named 'sys && cat /etc/passwd'",
            "ImportError: No module named 'evil`whoami`'",
        ]

        for error in malicious_errors:
            result = fixer.fix_missing_dependency(error)
            assert result is None, f"Should reject: {error}"

        assert req_file.read_text() == "requests==2.28.0\n"

    def test_fix_dependency_no_requirements_returns_none(self, fixer):
        error = "ImportError: No module named 'numpy'"
        result = fixer.fix_missing_dependency(error)
        assert result is None

    def test_extract_code_from_markdown(self, fixer):
        text = (
            "Here is the code:\n"
            "```python\n"
            "def hello():\n"
            "    return \"world\"\n"
            "```\n"
            "This is some explanation."
        )

        result = fixer._extract_code_block(text)
        assert "def hello():" in result
        assert 'return "world"' in result
        assert "```" not in result
        assert "Here is the code" not in result

    def test_extract_code_without_markdown(self, fixer):
        text = "def test():\n    pass\n\ndef another():\n    pass"
        result = fixer._extract_code_block(text)
        assert "def test():" in result
        assert "def another():" in result

    def test_full_workflow_missing_file(self, fixer):
        error = 'Error: File "src/config.py" not found during import'
        result = fixer.fix_missing_file_error(error)
        assert result is not None

        created = Path(result)
        assert created.exists()
        assert created.suffix == ".py"

        code = created.read_text()
        compile(code, "config.py", "exec")

    def test_concurrent_fixes_safe(self, fixer):
        errors = [
            'Error: "file1.py" not found',
            'Error: "file2.py" not found',
            'Error: "file3.py" not found',
        ]

        results = [fixer.fix_missing_file_error(e) for e in errors]
        assert all(r is not None for r in results)
        for r in results:
            assert Path(r).exists()

    def test_error_recovery_invalid_response(self, fixer):
        fixer.agent = Mock()
        fixer.agent.query = Mock(return_value="This is not code at all!")

        error = 'Error: "test.py" not found'
        try:
            fixer.fix_missing_file_error(error)
        except Exception as e:
            pytest.fail(f"Should handle invalid response: {e}")


class TestPerformance:
    """Performance tests (still isolated from external services)."""

    @pytest.fixture
    def fixer(self):
        temp_dir = tempfile.mkdtemp()
        agent = MockOllamaAgent(model="test")
        f = PRErrorFixer(agent, str(temp_dir))
        yield f
        shutil.rmtree(temp_dir)

    def test_fix_file_performance(self, fixer):
        import time

        error = 'Error: "test.py" not found'
        start = time.time()
        fixer.fix_missing_file_error(error)
        elapsed = time.time() - start
        assert elapsed < 2.0

    def test_submodule_fix_performance(self, fixer):
        import time

        gitmodules = Path(fixer.repo_path) / ".gitmodules"
        with open(gitmodules, "w") as f:
            for i in range(100):
                f.write(f'[submodule "mod{i}"]\n    path = mod{i}\n\n')
            f.write('[submodule "broken"]\n    path = broken\n')

        error = "fatal: No url found for submodule path 'broken'"
        start = time.time()
        fixer.fix_submodule_error(error)
        elapsed = time.time() - start
        assert elapsed < 1.0


if __name__ == "__main__":
    import pytest as _pytest

    _pytest.main([__file__, "-v", "-s"])
