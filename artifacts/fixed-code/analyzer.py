import re
from typing import Dict, List

class PRErrorAnalyzer:
    """Production-ready error analyzer for GitHub Actions logs"""

    def __init__(self, agent):
        """
        Initialize analyzer

        Args:
            agent: Ollama agent for AI-powered analysis
        """
        self.agent = agent
        self.error_patterns = [
            r"Error: (.+)",
            r"ERROR: (.+)",
            r"fatal: (.+)",
            r"Failed (.+)",
            r"Exception: (.+)",
            r"\[ERROR\] (.+)",
            r"ImportError: (.+)",
            r"SyntaxError: (.+)",
            r"ModuleNotFoundError: (.+)",
        ]

        self.warning_patterns = [
            r"Warning: (.+)",
            r"WARN: (.+)",
            r"\[WARN\] (.+)",
            r"DeprecationWarning: (.+)",
        ]

    def parse_github_actions_log(self, log_content: str) -> Dict[str, List[str]]:
        """
        Parse GitHub Actions log to extract errors and warnings

        Args:
            log_content: Raw log content

        Returns:
            Dict with 'errors' and 'warnings' lists
        """
        errors = []
        warnings = []

        for line in log_content.split('\n'):
            # Check errors
            for pattern in self.error_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    errors.append(line.strip())
                    break

            # Check warnings
            for pattern in self.warning_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    warnings.append(line.strip())
                    break

        return {
            "errors": errors,
            "warnings": warnings
        }

    def analyze_error(self, error: str) -> Dict[str, str]:
        """
        Analyze specific error using AI agent

        Args:
            error: Error message to analyze

        Returns:
            Dict with analysis results
        """
        prompt = f"""Analyze this error and provide:
1. Root cause
2. Suggested fix
3. Code changes needed

Error: {error}

Be concise and specific."""

        response = self.agent.query(prompt)

        # Sanitize the response to prevent injection attacks
        sanitized_response = self._sanitize_text(response)

        return {
            "error": error,
            "analysis": sanitized_response,
            "root_cause": self._extract_root_cause(sanitized_response),
            "suggested_fix": self._extract_fix(sanitized_response),
            "category": self.categorize_error(error),
            "severity": self.get_error_severity(error)
        }

    def categorize_error(self, error: str) -> str:
        """
        Categorize error type

        Args:
            error: Error message

        Returns:
            Error category string
        """
        error_lower = error.lower()

        # Git/submodule errors
        if 'submodule' in error_lower:
            return 'submodule_error'

        # Module/import errors
        if 'no module named' in error_lower or 'importerror' in error_lower or 'module' in error_lower:
            return 'missing_module'

        # File-related errors
        if 'not found' in error_lower or 'no such file' in error_lower:
            return 'missing_file'

        # Syntax errors
        if 'syntaxerror' in error_lower or 'invalid syntax' in error_lower:
            return 'syntax_error'

        # Permission errors
        if 'permission denied' in error_lower:
            return 'permission_error'

        # Network/timeout errors
        if 'timeout' in error_lower or 'timed out' in error_lower:
            return 'timeout_error'

        # Type errors
        if 'typeerror' in error_lower:
            return 'type_error'

        # Attribute errors
        if 'attributeerror' in error_lower:
            return 'attribute_error'

        return 'unknown'

    def get_error_severity(self, error: str) -> str:
        """
        Determine error severity

        Args:
            error: Error message

        Returns:
            Severity level: critical, high, medium, low
        """
        error_lower = error.lower()

        if 'fatal' in error_lower or 'critical' in error_lower:
            return 'critical'
        elif 'error' in error_lower:
            return 'high'
        elif 'warn' in error_lower:
            return 'low'
        else:
            return 'medium'

    def _extract_root_cause(self, analysis: str) -> str:
        """Extract root cause from analysis text"""
        lines = analysis.lower().split('\n')
        for line in lines:
            if 'root cause' in line or 'cause:' in line:
                return line.strip()
        return "Unknown"

    def _extract_fix(self, analysis: str) -> str:
        """Extract suggested fix from analysis text"""
        lines = analysis.lower().split('\n')
        for line in lines:
            if 'fix' in line or 'solution' in line:
                return line.strip()
        return "No fix suggested"

    def get_error_context(self, log_content: str, error_line: str, context_lines: int = 3) -> List[str]:
        """
        Get context lines around an error

        Args:
            log_content: Full log content
            error_line: The error line to find context for
            context_lines: Number of lines before/after to include

        Returns:
            List of context lines
        """
        lines = log_content.split('\n')

        try:
            error_index = lines.index(error_line)
            start = max(0, error_index - context_lines)
            end = min(len(lines), error_index + context_lines + 1)
            return lines[start:end]
        except ValueError:
            return []


class ErrorStatistics:
    """Track and analyze error statistics"""

    def __init__(self):
        self.error_counts = {}
        self.category_counts = {}
        self.severity_counts = {}

    def record_error(self, error: str, category: str, severity: str):
        """Record an error for statistics"""
        # Count by error message
        self.error_counts[error] = self.error_counts.get(error, 0) + 1

        # Count by category
        self.category_counts[category] = self.category_counts.get(category, 0) + 1

        # Count by severity
        self.severity_counts[severity] = self.severity_counts.get(severity, 0) + 1

    def get_most_common_errors(self, top_n: int = 5) -> List[tuple]:
        """Get most common errors"""
        sorted_errors = sorted(
            self.error_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_errors[:top_n]

    def get_summary(self) -> Dict:
        """Get summary statistics"""
        return {
            "total_errors": sum(self.error_counts.values()),
            "unique_errors": len(self.error_counts),
            "by_category": self.category_counts,
            "by_severity": self.severity_counts,
            "most_common": self.get_most_common_errors()
        }