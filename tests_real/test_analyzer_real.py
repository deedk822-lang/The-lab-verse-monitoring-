"""REAL Tests for PRErrorAnalyzer

These tests validate log parsing and error analysis behavior.

CI/CD ready:
- No merge artifacts
- No sys.path hacks
- Imports use the installed package namespace
"""

import pytest
from unittest.mock import Mock

from pr_fix_agent.analyzer import PRErrorAnalyzer


class TestPRErrorAnalyzerReal:
    """Real tests that validate parsing and analysis"""

    @pytest.fixture
    def mock_agent(self):
        agent = Mock()
        agent.query = Mock(
            return_value=(
                "Root cause: Missing dependency\n"
                "Suggested fix: Install the required package\n"
                "Code changes: Add to requirements.txt"
            )
        )
        return agent

    @pytest.fixture
    def analyzer(self, mock_agent):
        return PRErrorAnalyzer(mock_agent)

    def test_parse_empty_log(self, analyzer):
        result = analyzer.parse_github_actions_log("")
        assert result["errors"] == []
        assert result["warnings"] == []

    def test_parse_log_with_errors(self, analyzer):
        log = """
Build started
Error: Module not found
Some other output
Fatal: Repository not found
Build failed
"""
        result = analyzer.parse_github_actions_log(log)
        assert len(result["errors"]) >= 2
        assert any("Module not found" in e for e in result["errors"])
        assert any("Repository not found" in e for e in result["errors"])

    def test_parse_log_with_warnings(self, analyzer):
        log = """
Build started
Warning: Deprecated function used
Another line
WARN: File will be overwritten
Build completed
"""
        result = analyzer.parse_github_actions_log(log)
        assert len(result["warnings"]) >= 2
        assert any("Deprecated function" in w for w in result["warnings"])
        assert any("overwritten" in w for w in result["warnings"])

    def test_parse_log_mixed_errors_warnings(self, analyzer):
        log = """
Error: First error
Warning: First warning
Error: Second error
Warning: Second warning
Info: Just information
"""
        result = analyzer.parse_github_actions_log(log)
        assert len(result["errors"]) == 2
        assert len(result["warnings"]) == 2

    def test_parse_real_github_actions_log(self, analyzer):
        log = """
Run pytest tests/ -v --cov=.
============================= test session starts ==============================
collected 42 items

tests/test_main.py::test_import PASSED
tests/test_main.py::test_function FAILED

=================================== FAILURES ===================================
_________________________ test_function _________________________

    def test_function():
>       assert False
E       AssertionError

tests/test_main.py:10: AssertionError
============================= short test summary info ==========================
FAILED tests/test_main.py::test_function - AssertionError
Error: Process completed with exit code 1.
"""
        result = analyzer.parse_github_actions_log(log)
        assert len(result["errors"]) >= 1
        assert any("exit code 1" in e or "FAILED" in e for e in result["errors"])

    def test_parse_import_errors(self, analyzer):
        log = """
Traceback (most recent call last):
  File "main.py", line 1, in <module>
    import missing_module
ImportError: No module named 'missing_module'
"""
        result = analyzer.parse_github_actions_log(log)
        assert len(result["errors"]) >= 1
        assert any("missing_module" in e for e in result["errors"])

    def test_parse_syntax_errors(self, analyzer):
        log = """
  File "script.py", line 5
    def broken(
             ^
SyntaxError: invalid syntax
"""
        result = analyzer.parse_github_actions_log(log)
        assert len(result["errors"]) >= 1
        assert any("SyntaxError" in e or "invalid syntax" in e for e in result["errors"])

    def test_parse_case_insensitive(self, analyzer):
        log = """
error: Something failed
ERROR: Another failure
Error: Third failure
"""
        result = analyzer.parse_github_actions_log(log)
        assert len(result["errors"]) == 3

    def test_analyze_error_calls_agent(self, analyzer, mock_agent):
        error = "Error: File not found"
        analyzer.analyze_error(error)
        mock_agent.query.assert_called_once()
        call_prompt = mock_agent.query.call_args[0][0]
        assert "File not found" in call_prompt

    def test_analyze_error_returns_structure(self, analyzer):
        error = "ImportError: No module named 'requests'"
        result = analyzer.analyze_error(error)
        assert result["error"] == error
        assert "analysis" in result
        assert "root_cause" in result
        assert "suggested_fix" in result

    def test_categorize_missing_file(self, analyzer):
        for err in [
            'Error: "config.py" not found',
            'Error: No such file or directory: test.txt',
            'FileNotFoundError: [Errno 2] No such file',
        ]:
            assert analyzer.categorize_error(err) == "missing_file"

    def test_categorize_missing_module(self, analyzer):
        for err in [
            "ImportError: No module named 'numpy'",
            "ModuleNotFoundError: No module named 'requests'",
        ]:
            assert analyzer.categorize_error(err) == "missing_module"

    def test_categorize_syntax_error(self, analyzer):
        for err in ["SyntaxError: invalid syntax", "Error: Invalid syntax at line 10"]:
            assert analyzer.categorize_error(err) == "syntax_error"

    def test_severity_levels(self, analyzer):
        assert analyzer.get_error_severity("Fatal: System failure") == "critical"
        assert analyzer.get_error_severity("Error: Build failed") == "high"
        assert analyzer.get_error_severity("Warning: Deprecated") == "low"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
