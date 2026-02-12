"""
CORRECTED Test File - Uses Actual Package Name
Issue Fixed: Package name is pr_fix_agent, not src
"""

from unittest.mock import Mock

import pytest

# ✅ CORRECT: Import from pr_fix_agent (the actual package name)
from pr_fix_agent.analyzer import PRErrorAnalyzer


class TestPRErrorAnalyzerReal:
    """Real tests using correct package imports"""

    @pytest.fixture
    def mock_agent(self):
        """Mock agent to avoid HTTP calls"""
        agent = Mock()
        # Mocking query method to return a string response as expected by PRErrorAnalyzer
        agent.query = Mock(
            return_value="""Root cause: Missing dependency
Suggested fix: Install the required package
Code changes: Add to requirements.txt"""
        )
        return agent

    @pytest.fixture
    def analyzer(self, mock_agent):
        """Create analyzer with mock agent"""
        return PRErrorAnalyzer(mock_agent)

    def test_analyze_error_basic(self, analyzer):
        """Test: Analyze error returns structured results"""
        error = "ImportError: No module named 'requests'"
        result = analyzer.analyze_error(error)

        assert result["error"] == error[:200]
        assert "root_cause" in result
        assert "suggested_fix" in result
        assert "analysis" in result

    def test_extract_root_cause(self, analyzer):
        """Test: Root cause extraction preserves casing"""
        analysis = "Root cause: THE ISSUE IS HERE\nFix: DO THIS"
        result = analyzer._extract_root_cause(analysis)
        assert result == "Root cause: THE ISSUE IS HERE"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
