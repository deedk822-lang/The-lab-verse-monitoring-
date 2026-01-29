"""Error Analysis Components."""

import re
from pathlib import Path
from typing import Dict, List


class PRErrorAnalyzer:
    """Production-ready error analyzer for GitHub Actions logs."""

    def __init__(self, agent):
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
        errors: List[str] = []
        warnings: List[str] = []

        for line in log_content.split("\n"):
            for pattern in self.error_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    errors.append(line.strip())
                    break

            for pattern in self.warning_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    warnings.append(line.strip())
                    break

        return {"errors": errors, "warnings": warnings}

    def analyze_error(self, error: str) -> Dict[str, str]:
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
        for line in analysis.lower().split("\n"):
            if "root cause" in line or "cause:" in line:
                return line.strip()
        return "Unknown"

    def _extract_fix(self, analysis: str) -> str:
        for line in analysis.lower().split("\n"):
            if "fix" in line or "solution" in line:
                return line.strip()
        return "No fix suggested"


class OllamaAgent:
    """Ollama agent for AI-powered analysis and fixing."""

    def __init__(self, model: str = "codellama", url: str = "http://localhost:11434"):
        self.model = model
        self.url = url

    def query(self, prompt: str, temperature: float = 0.2) -> str:
        import requests

        response = requests.post(
            f"{self.url}/api/generate",
            json={"model": self.model, "prompt": prompt, "stream": False, "temperature": temperature},
            timeout=60,
        )
        response.raise_for_status()
        return response.json().get("response", "")


class PRErrorFixer:
    """Automated PR error fixing logic."""

    def __init__(self, agent, repo_path: str = "."):
        self.agent = agent
        self.repo_path = Path(repo_path)

    def fix_missing_file_error(self, error: str):
        file_match = re.search(r"['\"](.*?)['\"].*not found", error, re.IGNORECASE)
        if not file_match:
            return None

        filename = file_match.group(1)
        if ".." in filename or filename.startswith("/"):
            return None

        code = self.agent.query(f"Generate code for {filename}", temperature=0.1)
        file_path = self.repo_path / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)

        code_clean = self._extract_code_block(code)
        file_path.write_text(code_clean)
        return str(file_path)

    def fix_submodule_error(self, error: str):
        if "No url found for submodule" not in error:
            return None

        submodule_match = re.search(r"submodule path '(.+?)'", error)
        if not submodule_match:
            return None

        submodule_name = submodule_match.group(1)
        if ".." in submodule_name or "/" in submodule_name:
            return None

        gitmodules_path = self.repo_path / ".gitmodules"
        if not gitmodules_path.exists():
            return None

        content = gitmodules_path.read_text()
        pattern = rf'\[submodule "{re.escape(submodule_name)}"\].*?(?=\[|$)'
        new_content = re.sub(pattern, "", content, flags=re.DOTALL)
        gitmodules_path.write_text(new_content)
        return f"Removed broken submodule reference: {submodule_name}"

    def fix_missing_dependency(self, error: str):
        module_match = re.search(r"No module named ['\"](.*?)['\"]", error)
        if not module_match:
            return None

        module_name = module_match.group(1)
        if not re.match(r"^[a-zA-Z0-9_\-\.]+$", module_name):
            return None

        req_file = self.repo_path / "requirements.txt"
        if not req_file.exists():
            return None

        lines = [ln.strip() for ln in req_file.read_text().splitlines() if ln.strip()]
        normalized = module_name.lower()
        for ln in lines:
            # exact-ish match: name or name==... or name>=... etc.
            if ln.lower() == normalized or ln.lower().startswith(normalized + "==") or ln.lower().startswith(normalized + ">=") or ln.lower().startswith(normalized + "<="):
                return None

        with req_file.open("a") as f:
            f.write(f"\n{module_name}\n")

        return f"Added {module_name} to requirements.txt"

    def _extract_code_block(self, text: str) -> str:
        match = re.search(r"```(?:\w+)?\n(.*?)```", text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return text.strip()
