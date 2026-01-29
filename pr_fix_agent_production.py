#!/usr/bin/env python3
"""
PR Error-Fixing Agent using Ollama
Production-ready version with proper library structure
"""

import os
import json
import subprocess
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional
import requests

# Import from proper src/ directory
sys.path.insert(0, str(Path(__file__).parent / "src"))
from security import SecurityValidator, SecurityError
from analyzer import PRErrorAnalyzer


class OllamaAgent:
    """Agent that uses Ollama models for code analysis and fixing"""

    def __init__(self, model: str = "codellama", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"

    def query(self, prompt: str, temperature: float = 0.2) -> str:
        """Query Ollama with a prompt"""
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
            return response.json()["response"]
        except Exception as e:
            print(f"Error querying Ollama: {e}")
            return ""


class PRErrorFixer:
    """Automatically fixes common PR errors with security validation"""

    def __init__(self, agent: OllamaAgent, repo_path: str = "."):
        self.agent = agent
        self.repo_path = Path(repo_path)
        self.security = SecurityValidator(self.repo_path)

    def fix_missing_file_error(self, error: str) -> Optional[str]:
        """Fix errors related to missing files"""
        # Extract filename from error
        file_match = re.search(r"['\"](.*?)['\"].*not found", error, re.IGNORECASE)
        if not file_match:
            return None

        filename = file_match.group(1)

        # Security: Validate path
        try:
            file_path = self.security.validate_path(filename)
        except SecurityError as e:
            print(f"Security: Blocked path {filename}: {e}")
            return None

        # Security: Validate extension
        if not self.security.validate_file_extension(filename):
            print(f"Security: Blocked dangerous extension in {filename}")
            return None

        prompt = f"""Generate a minimal, working version of this file: {filename}

Based on the error context, create a basic implementation that will allow the CI/CD pipeline to pass.
Include only the essential code structure. Format your response as pure code with no explanations."""

        code = self.agent.query(prompt, temperature=0.1)

        # Create the file
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Clean up the response to extract just code
        code_clean = self._extract_code_block(code)

        with open(file_path, 'w') as f:
            f.write(code_clean)

        return str(file_path)

    def fix_submodule_error(self, error: str) -> Optional[str]:
        """Fix git submodule errors"""
        if "No url found for submodule" in error:
            submodule_match = re.search(r"submodule path '(.+?)'", error)
            if submodule_match:
                submodule_name = submodule_match.group(1)

                # Security: Validate submodule name
                if '..' in submodule_name or submodule_name.startswith('/'):
                    print(f"Security: Blocked dangerous submodule path: {submodule_name}")
                    return None

                try:
                    self.security.sanitize_input(submodule_name, max_length=100)
                except SecurityError as e:
                    print(f"Security: Blocked submodule {submodule_name}: {e}")
                    return None

                # Remove the submodule reference
                gitmodules_path = self.repo_path / ".gitmodules"
                if gitmodules_path.exists():
                    with open(gitmodules_path, 'r') as f:
                        content = f.read()

                    # Remove the submodule section
                    pattern = rf'\[submodule "{re.escape(submodule_name)}"\].*?(?=\[|$)'
                    new_content = re.sub(pattern, '', content, flags=re.DOTALL)

                    with open(gitmodules_path, 'w') as f:
                        f.write(new_content)

                    return f"Removed broken submodule reference: {submodule_name}"

        return None

    def fix_missing_dependency(self, error: str) -> Optional[str]:
        """Add missing dependencies to requirements files"""
        module_match = re.search(r"No module named ['\"](.*?)['\"]", error)
        if not module_match:
            return None

        module_name = module_match.group(1)

        # Security: Validate module name
        try:
            validated_module = self.security.validate_module_name(module_name)
        except SecurityError as e:
            print(f"Security: Blocked module {module_name}: {e}")
            return None

        # Check for requirements.txt
        req_file = self.repo_path / "requirements.txt"
        if req_file.exists():
            with open(req_file, 'r') as f:
                current_deps = f.read()

            if validated_module not in current_deps:
                with open(req_file, 'a') as f:
                    f.write(f"\n{validated_module}\n")
                return f"Added {validated_module} to requirements.txt"

        return None

    def _extract_code_block(self, text: str) -> str:
        """Extract code from markdown code blocks"""
        # Try to find code blocks
        code_block_match = re.search(r'```(?:\w+)?\n(.*?)```', text, re.DOTALL)
        if code_block_match:
            return code_block_match.group(1).strip()

        # If no code block, return cleaned text
        lines = text.split('\n')
        code_lines = [line for line in lines if not line.strip().startswith('#') or line.strip().startswith('#!/')]
        return '\n'.join(code_lines).strip()


class PRFixAgent:
    """Main agent that orchestrates PR error fixing"""

    def __init__(self, model: str = "codellama", repo_path: str = "."):
        self.ollama = OllamaAgent(model=model)
        self.analyzer = PRErrorAnalyzer(self.ollama)
        self.fixer = PRErrorFixer(self.ollama, repo_path)
        self.repo_path = Path(repo_path)

    def process_github_actions_log(self, log_file: str) -> Dict:
        """Process a GitHub Actions log file and fix errors"""
        with open(log_file, 'r') as f:
            log_content = f.read()

        # Parse errors
        issues = self.analyzer.parse_github_actions_log(log_content)

        results = {
            "errors_found": len(issues["errors"]),
            "warnings_found": len(issues["warnings"]),
            "fixes_applied": [],
            "analyses": []
        }

        print(f"\nFound {results['errors_found']} errors and {results['warnings_found']} warnings\n")

        # Analyze and fix each error
        for error in issues["errors"]:
            print(f"Analyzing: {error[:100]}...")

            # Get analysis
            analysis = self.analyzer.analyze_error(error)
            results["analyses"].append(analysis)

            # Attempt automatic fixes
            fix_result = None

            error_category = self.analyzer.categorize_error(error)

            if error_category == 'missing_file':
                fix_result = self.fixer.fix_missing_file_error(error)
            elif error_category == 'submodule_error':
                fix_result = self.fixer.fix_submodule_error(error)
            elif error_category == 'missing_module':
                fix_result = self.fixer.fix_missing_dependency(error)

            if fix_result:
                results["fixes_applied"].append(fix_result)
                print(f"  ✓ Applied fix: {fix_result}")
            else:
                print(f"  ℹ Manual intervention may be required")

        return results

    def generate_fix_report(self, results: Dict) -> str:
        """Generate a markdown report of the fixes"""
        report = f"""# PR Error Fix Report

## Summary
- **Errors Found:** {results['errors_found']}
- **Warnings Found:** {results['warnings_found']}
- **Automatic Fixes Applied:** {len(results['fixes_applied'])}

## Fixes Applied
"""
        for fix in results['fixes_applied']:
            report += f"\n- {fix}"

        report += "\n\n## Error Analyses\n"
        for i, analysis in enumerate(results['analyses'], 1):
            report += f"\n### Error {i}\n"
            report += f"**Error:** {analysis['error'][:200]}...\n\n"
            report += f"**Analysis:**\n{analysis['analysis']}\n\n"

        return report

    def create_fix_commit(self, message: str = "Auto-fix PR errors"):
        """Create a git commit with the fixes"""
        try:
            # Security: Use argument list instead of shell=True
            subprocess.run(
                ["git", "add", "."],
                cwd=self.repo_path,
                check=True,
                shell=False
            )
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.repo_path,
                check=True,
                shell=False
            )
            print(f"\n✓ Created commit: {message}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"\nFailed to create commit: {e}")
            return False


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="PR Error-Fixing Agent using Ollama")
    parser.add_argument("log_file", nargs='?', help="Path to GitHub Actions log file")
    parser.add_argument("--model", default="codellama", help="Ollama model to use")
    parser.add_argument("--repo-path", default=".", help="Path to repository")
    parser.add_argument("--commit", action="store_true", help="Create a git commit with fixes")
    parser.add_argument("--report", help="Path to save fix report")
    parser.add_argument("--health-check", action="store_true", help="Run health check")

    args = parser.parse_args()

    # Health check mode
    if args.health_check:
        print("🏥 Running health check...")
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            response.raise_for_status()
            print("✅ Ollama is healthy")
            return 0
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return 1

    # Require log file for normal operation
    if not args.log_file:
        parser.print_help()
        return 1

    # Initialize agent
    agent = PRFixAgent(model=args.model, repo_path=args.repo_path)

    print(f"🤖 PR Fix Agent starting...")
    print(f"   Model: {args.model}")
    print(f"   Log file: {args.log_file}")
    print(f"   Repository: {args.repo_path}\n")

    # Process the log
    results = agent.process_github_actions_log(args.log_file)

    # Generate report
    report = agent.generate_fix_report(results)
    print("\n" + "="*60)
    print(report)
    print("="*60)

    # Save report if requested
    if args.report:
        with open(args.report, 'w') as f:
            f.write(report)
        print(f"\n✓ Report saved to {args.report}")

    # Create commit if requested
    if args.commit and results['fixes_applied']:
        agent.create_fix_commit()

    print(f"\n✅ Processing complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
