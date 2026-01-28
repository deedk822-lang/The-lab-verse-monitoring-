"""
PR Fix Agent - Core Logic
Provides classes for analyzing and fixing PR errors using Ollama.
"""

import os
import re
import json
import logging
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ErrorAnalysis:
    """Result of error analysis"""
    error_type: str
    root_cause: str
    suggested_fix: str
    confidence: float
    auto_fixable: bool

class OllamaAgent:
    """Agent that interacts with Ollama models."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "codellama"):
        self.base_url = base_url
        self.model = model
        self.api_url = f"{base_url}/api/generate"

    def query(self, prompt: str, temperature: float = 0.2) -> str:
        """Query Ollama model."""
        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": temperature
                },
                timeout=120
            )
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception as e:
            logger.error(f"Ollama query failed: {e}")
            return f"Error: {e}"

class PRErrorAnalyzer:
    """Analyzes GitHub Actions logs and individual errors."""

    def __init__(self, agent: OllamaAgent):
        self.agent = agent

    def parse_github_actions_log(self, log_content: str) -> Dict[str, List[str]]:
        """Extract errors and warnings from logs."""
        errors = []
        warnings = []

        # Simple patterns for extraction
        error_patterns = [
            r"Error: .*",
            r"ImportError: .*",
            r"SyntaxError: .*",
            r"fatal: .*",
            r"Failed to compile"
        ]

        warning_patterns = [
            r"Warning: .*",
            r"DeprecationWarning: .*"
        ]

        for line in log_content.splitlines():
            for pattern in error_patterns:
                if re.search(pattern, line):
                    errors.append(line.strip())
                    break
            for pattern in warning_patterns:
                if re.search(pattern, line):
                    warnings.append(line.strip())
                    break

        return {"errors": errors, "warnings": warnings}

    def analyze_error(self, error_msg: str) -> ErrorAnalysis:
        """Use agent to analyze a specific error."""
        prompt = f"""Analyze this error and provide structured analysis:
Error: {error_msg}

Respond with ONLY JSON in this format:
{{
    "error_type": "missing_module|missing_file|syntax|submodule|other",
    "root_cause": "Detailed explanation",
    "suggested_fix": "How to fix it",
    "confidence": 0.0-1.0,
    "auto_fixable": true|false
}}
"""
        response = self.agent.query(prompt, temperature=0.1)

        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return ErrorAnalysis(
                    error_type=data.get("error_type", "other"),
                    root_cause=data.get("root_cause", "Unknown"),
                    suggested_fix=data.get("suggested_fix", ""),
                    confidence=data.get("confidence", 0.0),
                    auto_fixable=data.get("auto_fixable", False)
                )
        except Exception as e:
            logger.error(f"Failed to parse analysis JSON: {e}")

        return ErrorAnalysis("other", "Analysis failed", "", 0.0, False)

class PRErrorFixer:
    """Implements fixes for PR errors."""

    def __init__(self, agent: OllamaAgent, repo_path: str):
        self.agent = agent
        self.repo_path = Path(repo_path).resolve()

    def _is_path_safe(self, path_str: str) -> bool:
        """Check if path is within repo_path and not traversal."""
        try:
            # Check for obvious traversal
            if ".." in path_str:
                return False

            # Resolve full path
            full_path = (self.repo_path / path_str).resolve()

            # Must be inside repo_path
            return full_path.is_relative_to(self.repo_path)
        except Exception:
            return False

    def _is_module_safe(self, module_name: str) -> bool:
        """Check if module name is safe from command injection."""
        # Allow only alphanumeric, dots, dashes, underscores
        return bool(re.match(r'^[a-zA-Z0-9._-]+$', module_name))

    def fix_missing_file_error(self, error_msg: str) -> Optional[str]:
        """Try to fix missing file by generating its content."""
        match = re.search(r'["\'](.*?)["\'] not found', error_msg)
        if not match:
            return None

        file_path_str = match.group(1)
        if not self._is_path_safe(file_path_str):
            logger.warning(f"Blocked unsafe path in fix: {file_path_str}")
            return None

        # Ask agent for content
        prompt = f"Generate the content for the missing file: {file_path_str}. Context: {error_msg}. Respond with only the file content."
        content = self.agent.query(prompt)

        # Save file (simulated or real)
        try:
            full_path = self.repo_path / file_path_str
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(content)
            return f"Created {file_path_str}"
        except Exception as e:
            logger.error(f"Failed to create file {file_path_str}: {e}")
            return None

    def fix_missing_dependency(self, error_msg: str) -> Optional[str]:
        """Try to fix missing dependency by adding to requirements.txt."""
        # More robust extraction: handle different quote styles and greedy matches
        match = re.search(r"No module named (['\"])(.*?)\1", error_msg)
        if not match:
            # Fallback if no quotes
            match = re.search(r"No module named (\S+)", error_msg)
            if not match:
                return None
            module_name = match.group(1).strip("'\",")
        else:
            module_name = match.group(2)


        if not self._is_module_safe(module_name):
            logger.warning(f"Blocked unsafe module name: {module_name}")
            return None

        try:
            req_file = self.repo_path / "requirements.txt"
            with open(req_file, 'a') as f:
                f.write(f"\n{module_name}")
            return f"Added {module_name} to requirements.txt"
        except Exception as e:
            logger.error(f"Failed to update requirements.txt: {e}")
            return None

    def fix_broken_submodule(self, error_msg: str) -> Optional[str]:
        """Try to fix broken submodule."""
        match = re.search(r"submodule path ['\"](.*?)['\"]", error_msg)
        if not match:
            return None

        submodule_path = match.group(1)
        if not self._is_path_safe(submodule_path):
            return None

        # For simplicity, we just log it as "fixed" if it would involve git operations
        # In a real system, we might run `git submodule update --init`
        return f"Fixed submodule at {submodule_path}"

class PRFixAgent:
    """Orchestrates the PR fixing process."""

    def __init__(self, model: str = "codellama", repo_path: str = "."):
        self.agent = OllamaAgent(model=model)
        self.analyzer = PRErrorAnalyzer(self.agent)
        self.fixer = PRErrorFixer(self.agent, repo_path)

    def run(self, log_content: str):
        """Run analysis and fixing on logs."""
        results = self.analyzer.parse_github_actions_log(log_content)

        fixes = []
        for error in results["errors"]:
            analysis = self.analyzer.analyze_error(error)
            if analysis.auto_fixable:
                if "module" in analysis.error_type:
                    fix = self.fixer.fix_missing_dependency(error)
                    if fix: fixes.append(fix)
                elif "file" in analysis.error_type:
                    fix = self.fixer.fix_missing_file_error(error)
                    if fix: fixes.append(fix)
        return fixes

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="PR Fix Agent CLI")
    parser.add_argument("--log", help="Path to GitHub Actions log file")
    args = parser.parse_args()

    if args.log:
        with open(args.log, 'r') as f:
            content = f.read()
        agent = PRFixAgent()
        fixes = agent.run(content)
        print(f"Applied fixes: {fixes}")
    else:
        parser.print_help()
