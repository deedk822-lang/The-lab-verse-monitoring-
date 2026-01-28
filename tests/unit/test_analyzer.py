"""Tests for error analysis functionality."""

import pytest
from unittest.mock import Mock, patch
from pr_fix_agent import PRErrorAnalyzer, OllamaAgent

class TestPRErrorAnalyzer:
    """Test error analyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create error analyzer."""
        agent = OllamaAgent()
        return PRErrorAnalyzer(agent)

    def test_parse_github_actions_log_no_errors(self, analyzer):
        """Test parsing log with no errors."""
        log = "Build successful\nAll tests passed"
        result = analyzer.parse_github_actions_log(log)
        assert len(result["errors"]) == 0

    def test_parse_github_actions_log_with_errors(self, analyzer):
        """Test parsing log with errors."""
        log = "Build failed\nError: Module not found\nFailed to compile"
        result = analyzer.parse_github_actions_log(log)
        assert len(result["errors"]) == 2

    def test_parse_github_actions_log_with_warnings(self, analyzer):
        """Test parsing log with warnings."""
        log = "Warning: Deprecated API\nBuild completed"
        result = analyzer.parse_github_actions_log(log)
        assert len(result["warnings"]) == 1

    def test_parse_missing_file_error(self, analyzer):
        """Test parsing missing file error."""
        log = 'Error: "test.py" not found'
        result = analyzer.parse_github_actions_log(log)
        assert len(result["errors"]) == 1
        assert "not found" in result["errors"][0]

    def test_analyze_error_with_json_response(self, analyzer):
        """Test error analysis with JSON response."""
        mock_res = '{"error_type": "missing_module", "root_cause": "Missing numpy", "suggested_fix": "pip install numpy", "confidence": 0.9, "auto_fixable": true}'
        with patch.object(OllamaAgent, 'query', return_value=mock_res):
            analysis = analyzer.analyze_error("No module named numpy")
            assert analysis.error_type == "missing_module"
            assert analysis.auto_fixable is True
