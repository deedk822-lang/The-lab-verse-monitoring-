"""
Error Analysis Components
Proper library structure for error parsing and analysis
"""

import re
from pathlib import Path
from typing import Dict, List, Optional


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

        return {
            "error": error,
            "analysis": response,
            "root_cause": self._extract_root_cause(response),
            "suggested_fix": self._extract_fix(response),
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

        # File-related errors
        if 'not found' in error_lower or 'no such file' in error_lower:
            return 'missing_file'

        # Module/import errors
        if 'no module named' in error_lower or 'importerror' in error_lower:
            return 'missing_module'

        # Syntax errors
        if 'syntaxerror' in error_lower or 'invalid syntax' in error_lower:
            return 'syntax_error'

        # Git/submodule errors
        if 'submodule' in error_lower:
            return 'submodule_error'

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
        elif 'warning' in error_lower:
            return 'low'
        else:
            return 'medium'

    def _extract_root_cause(self, analysis: str) -> str:
        """
        Extract root cause PRESERVING original casing

        FIXED: Don't lowercase the entire analysis
        """
        for line in analysis.split('\n'):
            # ✅ FIX: Check lowercase but return original
            if 'root cause' in line.lower() or 'cause:' in line.lower():
                return line.strip()  # Original casing preserved
        return "Unknown"

    def _extract_fix(self, analysis: str) -> str:
        """
        Extract fix PRESERVING original casing

        FIXED: Don't lowercase the entire analysis
        """
        for line in analysis.split('\n'):
            # ✅ FIX: Check lowercase but return original
            if 'fix' in line.lower() or 'solution' in line.lower():
                return line.strip()  # Original casing preserved
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


class OllamaAgent:
    """Ollama agent for AI-powered analysis and fixing"""
    def __init__(self, model="codellama", url="http://localhost:11434"):
        self.model = model
        self.url = url

    def query(self, prompt, temperature=0.2):
        """Query Ollama model"""
        import requests
        try:
            response = requests.post(
                f"{self.url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": temperature
                },
                timeout=60
            )
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception as e:
            return f"Error: {e}"


class PRErrorFixer:
    """Automated PR error fixing logic"""
    def __init__(self, agent, repo_path="."):
        self.agent = agent
        self.repo_path = Path(repo_path)

    def fix_missing_file_error(self, error):
        """Fix missing file error by generating content"""
        file_match = re.search(r"['\"](.*?)['\"].*not found", error, re.IGNORECASE)
        if not file_match:
            return None

        filename = file_match.group(1)

        # Security: Block path traversal
        if ".." in filename or filename.startswith("/"):
            return None

        prompt = f"Generate code for {filename}"
        code = self.agent.query(prompt, temperature=0.1)

        file_path = self.repo_path / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)

        code_clean = self._extract_code_block(code)

        with open(file_path, 'w') as f:
            f.write(code_clean)

        return str(file_path)

    def fix_submodule_error(self, error):
        """Fix broken submodule references"""
        if "No url found for submodule" in error:
            submodule_match = re.search(r"submodule path '(.+?)'", error)
            if submodule_match:
                submodule_name = submodule_match.group(1)

                # Security: Block path traversal
                if ".." in submodule_name or "/" in submodule_name:
                    return None

                gitmodules_path = self.repo_path / ".gitmodules"
                if gitmodules_path.exists():
                    with open(gitmodules_path, 'r') as f:
                        content = f.read()

                    pattern = rf'\[submodule "{submodule_name}"\].*?(?=\[|$)'
                    new_content = re.sub(pattern, '', content, flags=re.DOTALL)

                    with open(gitmodules_path, 'w') as f:
                        f.write(new_content)

                    return f"Removed broken submodule reference: {submodule_name}"

        return None

    def fix_missing_dependency(self, error):
        """Fix missing Python dependency"""
        module_match = re.search(r"No module named ['\"](.*?)['\"]", error)
        if not module_match:
            return None

        module_name = module_match.group(1)

        # Security: Validate module name
        if not re.match(r'^[a-zA-Z0-9_\-\.]+$', module_name):
            return None

        req_file = self.repo_path / "requirements.txt"
        if req_file.exists():
            with open(req_file, 'r') as f:
                current_deps = f.read()

            if module_name not in current_deps:
                with open(req_file, 'a') as f:
                    f.write(f"\n{module_name}\n")
                return f"Added {module_name} to requirements.txt"

        return None

    def _extract_code_block(self, text):
        """Extract code from markdown blocks"""
        code_block_match = re.search(r'```(?:\w+)?\n(.*?)```', text, re.DOTALL)
        if code_block_match:
            return code_block_match.group(1).strip()
        return text.strip()
