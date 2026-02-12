"""
REAL Tests for PRErrorAnalyzer
Tests actual log parsing and error analysis
"""

from unittest.mock import Mock

import pytest

# Conventional import from src
from pr_fix_agent.analyzer import PRErrorAnalyzer

# ============================================================================
# REAL TESTS
# ============================================================================


class TestPRErrorAnalyzerReal:
    """Real tests that validate actual parsing and analysis"""

    @pytest.fixture
    def mock_agent(self):
        """Create mock agent"""
        agent = Mock()
        agent.query = Mock(
            return_value="""Root cause: Missing dependency
Suggested fix: Install the required package
Code changes: Add to requirements.txt"""
        )
        return agent

    @pytest.fixture
    def analyzer(self, mock_agent):
        """Create analyzer instance"""
        return PRErrorAnalyzer(mock_agent)

    # ========================================================================
    # Log Parsing Tests
    # ========================================================================

    def test_parse_empty_log(self, analyzer):
        """Test: Empty log returns empty results"""
        log = ""

        result = analyzer.parse_github_actions_log(log)

        assert result["errors"] == []
        assert result["warnings"] == []

    def test_parse_log_with_errors(self, analyzer):
        """Test: Extracts actual errors from log"""
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
        """Test: Extracts warnings from log"""
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
        """Test: Separates errors and warnings correctly"""
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
        # Info should not be in either category

    def test_parse_real_github_actions_log(self, analyzer):
        """Test: Parses actual GitHub Actions log format"""
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
        """Test: Detects import errors"""
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
        """Test: Detects syntax errors"""
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
        """Test: Parsing is case-insensitive"""
        log = """
error: Something failed
ERROR: Another failure
Error: Third failure
"""

        result = analyzer.parse_github_actions_log(log)

        # Should find all three variants
        assert len(result["errors"]) == 3

    def test_parse_multiline_errors(self, analyzer):
        """Test: Handles multiline error messages"""
        log = """
Error: Failed to execute command
  Caused by: Network timeout
  Additional info: Check connectivity
"""

        result = analyzer.parse_github_actions_log(log)

        # Should at least get the first line
        assert len(result["errors"]) >= 1
        assert any("Failed to execute" in e for e in result["errors"])

    # ========================================================================
    # Error Analysis Tests
    # ========================================================================

    def test_analyze_error_calls_agent(self, analyzer, mock_agent):
        """Test: Calls agent with correct prompt"""
        error = "Error: File not found"

        result = analyzer.analyze_error(error)

        # Verify agent was called
        mock_agent.query.assert_called_once()
        call_args = mock_agent.query.call_args[0][0]
        assert "File not found" in call_args
        assert "Root cause" in call_args or "fix" in call_args.lower()

    def test_analyze_error_returns_structure(self, analyzer):
        """Test: Returns structured analysis"""
        error = "ImportError: No module named 'requests'"

        result = analyzer.analyze_error(error)

        assert "error" in result
        assert "analysis" in result
        assert result["error"] == error
        assert isinstance(result["analysis"], str)

    def test_analyze_error_extracts_root_cause(self, analyzer):
        """Test: Extracts root cause from analysis"""
        error = "Error: Test"

        result = analyzer.analyze_error(error)

        assert "root_cause" in result
        assert isinstance(result["root_cause"], str)

    def test_analyze_error_extracts_fix(self, analyzer):
        """Test: Extracts suggested fix"""
        error = "Error: Test"

        result = analyzer.analyze_error(error)

        assert "suggested_fix" in result
        assert isinstance(result["suggested_fix"], str)

    # ========================================================================
    # Error Categorization Tests
    # ========================================================================

    def test_categorize_missing_file(self, analyzer):
        """Test: Categorizes missing file errors"""
        errors = [
            'Error: "config.py" not found',
            "Error: No such file or directory: test.txt",
            "FileNotFoundError: [Errno 2] No such file",
        ]

        for error in errors:
            category = analyzer.categorize_error(error)
            assert category == "missing_file"

    def test_categorize_missing_module(self, analyzer):
        """Test: Categorizes import errors"""
        errors = [
            "ImportError: No module named 'numpy'",
            "ModuleNotFoundError: No module named 'requests'",
            "ImportError: Cannot import module 'flask'",
        ]

        for error in errors:
            category = analyzer.categorize_error(error)
            assert category == "missing_module"

    def test_categorize_syntax_error(self, analyzer):
        """Test: Categorizes syntax errors"""
        errors = [
            "SyntaxError: invalid syntax",
            "Error: Invalid syntax at line 10",
            "SyntaxError: unexpected EOF",
        ]

        for error in errors:
            category = analyzer.categorize_error(error)
            assert category == "syntax_error"

    def test_categorize_submodule_error(self, analyzer):
        """Test: Categorizes submodule errors"""
        errors = ["fatal: submodule path 'vendor' error", "Error: Submodule 'lib' issue"]

        for error in errors:
            category = analyzer.categorize_error(error)
            assert category == "submodule_error"

    def test_categorize_unknown(self, analyzer):
        """Test: Returns unknown for unrecognized errors"""
        error = "Something completely different happened"

        category = analyzer.categorize_error(error)

        assert category == "unknown"

    # ========================================================================
    # Severity Detection Tests
    # ========================================================================

    def test_severity_critical(self, analyzer):
        """Test: Detects critical severity"""
        errors = ["Fatal: System failure", "CRITICAL: Database corrupted"]

        for error in errors:
            severity = analyzer.get_error_severity(error)
            assert severity == "critical"

    def test_severity_high(self, analyzer):
        """Test: Detects high severity (regular errors)"""
        errors = ["Error: Build failed", "ERROR: Test failed"]

        for error in errors:
            severity = analyzer.get_error_severity(error)
            assert severity == "high"

    def test_severity_low(self, analyzer):
        """Test: Detects low severity (warnings)"""
        errors = ["Warning: Deprecated function", "DeprecationWarning: Configuration issue"]

        for error in errors:
            severity = analyzer.get_error_severity(error)
            assert severity == "low"

    # ========================================================================
    # Integration Tests
    # ========================================================================

    def test_full_workflow(self, analyzer):
        """Test: Complete analysis workflow"""
        # Real log excerpt
        log = """
##[group]Run pytest tests/
pytest tests/ -v --cov=.
##[endgroup]
============================= test session starts ==============================
Error: File "/home/runner/work/project/src/config.py" not found
ImportError: No module named 'requests'
FAILED tests/test_main.py::test_function - AssertionError
"""

        # Parse
        result = analyzer.parse_github_actions_log(log)

        assert len(result["errors"]) >= 2

        # Analyze first error
        if result["errors"]:
            analysis = analyzer.analyze_error(result["errors"][0])

            assert "error" in analysis
            assert "analysis" in analysis
            assert isinstance(analysis["analysis"], str)

    def test_performance_large_log(self, analyzer):
        """Test: Handles large logs efficiently"""
        import time

        # Create large log (10,000 lines)
        log_lines = []
        for i in range(10000):
            if i % 100 == 0:
                log_lines.append(f"Error: Test error {i}")
            else:
                log_lines.append(f"Info: Normal log line {i}")

        log = "\n".join(log_lines)

        start = time.time()
        result = analyzer.parse_github_actions_log(log)
        elapsed = time.time() - start

        # Should complete quickly
        assert elapsed < 1.0

        # Should find all errors
        assert len(result["errors"]) == 100

    def test_edge_case_empty_lines(self, analyzer):
        """Test: Handles empty lines correctly"""
        log = """

Error: First error

Warning: First warning


Error: Second error

"""

        result = analyzer.parse_github_actions_log(log)

        assert len(result["errors"]) == 2
        assert len(result["warnings"]) == 1

    def test_edge_case_special_characters(self, analyzer):
        """Test: Handles special characters in errors"""
        log = """
Error: File "path/with spaces/file.py" not found
Error: Failed to parse JSON: {"key": "value"}
Error: Regex pattern failed: [a-zA-Z]+
"""

        result = analyzer.parse_github_actions_log(log)

        assert len(result["errors"]) == 3
        # Should preserve special characters
        assert any("spaces" in e for e in result["errors"])
        assert any("JSON" in e for e in result["errors"])


# ============================================================================
# Statistical Analysis Tests
# ============================================================================


class TestStatisticalAnalysis:
    """Test statistical analysis capabilities"""

    @pytest.fixture
    def analyzer(self):
        agent = Mock()
        agent.query = Mock(return_value="Analysis result")
        return PRErrorAnalyzer(agent)

    def test_error_frequency_analysis(self, analyzer):
        """Test: Can analyze error frequency"""
        logs = [
            "ImportError: No module named 'requests'",
            "ImportError: No module named 'numpy'",
            "ImportError: No module named 'requests'",
            "Error: File not found",
            "ImportError: No module named 'requests'",
        ]

        log = "\n".join(logs)
        result = analyzer.parse_github_actions_log(log)

        # Count occurrences
        error_types = {}
        for error in result["errors"]:
            category = analyzer.categorize_error(error)
            error_types[category] = error_types.get(category, 0) + 1

        # Should identify requests as most common
        assert error_types.get("missing_module", 0) >= 3

    def test_error_pattern_detection(self, analyzer):
        """Test: Detects patterns in errors"""
        log = """
Error: Connection timeout to server1
Error: Connection timeout to server2
Error: Connection timeout to server3
Error: File not found
"""

        result = analyzer.parse_github_actions_log(log)

        # Count timeout errors
        timeout_errors = [e for e in result["errors"] if "timeout" in e.lower()]

        assert len(timeout_errors) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
