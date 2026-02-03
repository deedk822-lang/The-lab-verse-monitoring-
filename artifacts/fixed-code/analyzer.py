"""
Error Analysis Components
Proper library structure for error parsing and analysis
"""

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

        try:
            response = self.agent.query(prompt)
            return {
                "error": error,
                "analysis": response,
                "root_cause": self._extract_root_cause(response),
                "suggested_fix": self._extract_fix(response),
                "category": self.categorize_error(error),
                "severity": self.get_error_severity(error)
            }
        except Exception as e:
            return {
                "error": error,
                "analysis": f"An error occurred while analyzing the error: {e}",
                "root_cause": None,
                "suggested_fix": None,
                "category": None,
                "severity": None
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
            Error severity string
        """
        # Example: Using a simple heuristic for severity determination
        if 'permission denied' in error.lower():
            return 'low'
        elif 'timeout' in error.lower():
            return 'medium'
        else:
            return 'high'

    def _extract_root_cause(self, response):
        # Extract root cause from AI response
        match = re.search(r"Root cause: (.+)", response)
        if match:
            return match.group(1).strip()

    def _extract_fix(self, response):
        # Extract suggested fix from AI response
        match = re.search(r"Suggested fix: (.+)", response)
        if match:
            return match.group(1).strip()