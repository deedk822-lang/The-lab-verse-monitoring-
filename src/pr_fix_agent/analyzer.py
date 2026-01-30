"""
Error Analysis Components
Proper library structure for error parsing and analysis
"""

import re
from pathlib import Path
from typing import Dict, List

from .security import SecurityError, SecurityValidator


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
        """Parse GitHub Actions log to extract errors and warnings."""
        errors: List[str] = []
        warnings: List[str] = []

        for line in log_content.split("\n"):
            for pattern in self.error_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    errors.append(line.strip())
                    break

            for pattern in self.warning_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    warnings.append(line.strip())
                    break

        return {"errors": errors, "warnings": warnings}

    def analyze_error(self, error: str) -> Dict[str, str]:
        """Analyze specific error using AI agent."""
        prompt = f"""Analyze this error and provide:
1. Root cause
2. Suggested fix
3. Code changes needed

Error: {error}

Be concise and specific."""

        try:
            response = self.agent.query(prompt)
        except Exception as e:
            return {
                "error": error,
                "analysis": "",
                "analysis_error": str(e),
                "root_cause": "Unknown",
                "suggested_fix": "No fix suggested",
                "category": self.categorize_error(error),
                "severity": self.get_error_severity(error),
            }

        return {
            "error": error,
            "analysis": response,
            "root_cause": self._extract_root_cause(response),
            "suggested_fix": self._extract_fix(response),
            "category": self.categorize_error(error),
            "severity": self.get_error_severity(error),
        }

    def categorize_error(self, error: str) -> str:
        error_lower = error.lower()

        if "not found" in error_lower or "no such file" in error_lower:
            return "missing_file"

        if "no module named" in error_lower or "importerror" in error_lower:
            return "missing_module"

        if "syntaxerror" in error_lower or "invalid syntax" in error_lower:
            return "syntax_error"

        if "submodule" in error_lower:
            return "submodule_error"

        if "permission denied" in error_lower:
            return "permission_error"

        if "timeout" in error_lower or "timed out" in error_lower:
            return "timeout_error"

        if "typeerror" in error_lower:
            return "type_error"

        if "attributeerror" in error_lower:
            return "attribute_error"

        return "unknown"

    def get_error_severity(self, error: str) -> str:
        error_lower = error.lower()

        if "fatal" in error_lower or "critical" in error_lower:
            return "critical"
        if "error" in error_lower:
            return "high"
        if "warning" in error_lower:
            return "low"
        return "medium"

    def _extract_root_cause(self, analysis: str) -> str:
        """Extract root cause from analysis text (preserve original casing)."""
        for line in analysis.split("\n"):
            lower_line = line.lower()
            if "root cause" in lower_line or "cause:" in lower_line:
                return line.strip()
        return "Unknown"

    def _extract_fix(self, analysis: str) -> str:
        """Extract suggested fix from analysis text (preserve original casing)."""
        for line in analysis.split("\n"):
            lower_line = line.lower()
            if "fix" in lower_line or "solution" in lower_line:
                return line.strip()
        return "No fix suggested"

    def get_error_context(self, log_content: str, error_line: str, context_lines: int = 3) -> List[str]:
        """Get context lines around an error."""
        lines = log_content.split("\n")

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
        self.error_counts[error] = self.error_counts.get(error, 0) + 1
        self.category_counts[category] = self.category_counts.get(category, 0) + 1
        self.severity_counts[severity] = self.severity_counts.get(severity, 0) + 1

    def get_most_common_errors(self, top_n: int = 5):
        sorted_errors = sorted(self.error_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_errors[:top_n]

    def get_summary(self) -> Dict:
        return {
            "total_errors": sum(self.error_counts.values()),
            "unique_errors": len(self.error_counts),
            "by_category": self.category_counts,
            "by_severity": self.severity_counts,
            "most_common": self.get_most_common_errors(),
        }


class OllamaAgent:
    """Ollama agent for AI-powered analysis and fixing"""

    def __init__(self, model: str = "codellama", url: str = "http://localhost:11434"):
        self.model = model
        self.url = url

    def query(self, prompt: str, temperature: float = 0.2) -> str:
        """Query Ollama model.

        Raises an exception on failure so callers can distinguish a real model response
        from an error.
        """
        import requests

        response = requests.post(
            f"{self.url}/api/generate",
            json={"model": self.model, "prompt": prompt, "stream": False, "temperature": temperature},
            timeout=60,
        )
        response.raise_for_status()
        return response.json().get("response", "")


class PRErrorFixer:
    """Automated PR error fixing logic"""

    def __init__(self, agent, repo_path: str = "."):
        self.agent = agent
        self.repo_path = Path(repo_path)
        self.security = SecurityValidator(self.repo_path)

    def fix_missing_file_error(self, error: str):
        """Fix missing file error by generating content."""
        file_match = re.search(r"['\"](.*?)['\"].*not found", error, re.IGNORECASE)
        if not file_match:
            return None

        filename = file_match.group(1)

        try:
            file_path = self.security.validate_path(filename)
        except SecurityError:
            return None

        prompt = f"Generate code for {filename}"
        code = self.agent.query(prompt, temperature=0.1)

        file_path.parent.mkdir(parents=True, exist_ok=True)

        code_clean = self._extract_code_block(code)
        file_path.write_text(code_clean)

        return str(file_path)

    def fix_submodule_error(self, error: str):
        """Fix broken submodule references."""
        if "No url found for submodule" in error:
            submodule_match = re.search(r"submodule path '(.+?)'", error)
            if submodule_match:
                submodule_name = submodule_match.group(1)

                # Security: Block traversal or nested paths
                if ".." in submodule_name or "/" in submodule_name:
                    return None

                gitmodules_path = self.repo_path / ".gitmodules"
                if gitmodules_path.exists():
                    content = gitmodules_path.read_text()
                    pattern = rf'\[submodule "{re.escape(submodule_name)}"\].*?(?=\[|$)'
                    new_content = re.sub(pattern, "", content, flags=re.DOTALL)
                    gitmodules_path.write_text(new_content)
                    return f"Removed broken submodule reference: {submodule_name}"

        return None

    def _normalize_requirement_name(self, line: str) -> str:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            return ""

        token = re.split(r"[<>=\[;]", stripped, maxsplit=1)[0].strip().lower()
        return token

    def fix_missing_dependency(self, error: str):
        """Fix missing Python dependency by adding it to requirements.txt if absent."""
        module_match = re.search(r"No module named ['\"](.*?)['\"]", error)
        if not module_match:
            return None

        module_name = module_match.group(1)
        try:
            module_name = self.security.validate_module_name(module_name)
        except SecurityError:
            return None

        req_file = self.repo_path / "requirements.txt"
        if not req_file.exists():
            return None

        wanted = module_name.strip().lower()
        existing = set()
        for line in req_file.read_text().splitlines():
            name = self._normalize_requirement_name(line)
            if name:
                existing.add(name)

        if wanted not in existing:
            with open(req_file, "a", encoding="utf-8") as f:
                f.write(f"\n{module_name}\n")
            return f"Added {module_name} to requirements.txt"

        return None

    def _extract_code_block(self, text: str) -> str:
        """Extract code from markdown blocks."""
        code_block_match = re.search(r"```(?:\w+)?\n(.*?)```", text, re.DOTALL)
        if code_block_match:
            return code_block_match.group(1).strip()
        return text.strip()
