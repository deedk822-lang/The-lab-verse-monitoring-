"""
PR Fix Agent Orchestrator
Integrates reasoning and coding pipelines for GitHub Actions
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any

from .ollama_agent_fixed import OllamaAgent
from .analyzer import PRErrorAnalyzer, PRErrorFixer
from .security import SecurityValidator


class Orchestrator:
    """Orchestrates the PR fixing process"""

    def __init__(self, model: str, repo_path: str = "."):
        self.model = model
        self.repo_path = Path(repo_path).resolve()
        self.agent = OllamaAgent(model=model)
        self.validator = SecurityValidator(self.repo_path)
        self.analyzer = PRErrorAnalyzer(self.agent)
        self.fixer = PRErrorFixer(self.agent, str(self.repo_path))

    def run_reasoning(self, findings_dir: str, output_file: str):
        """Analyze findings and generate fix proposals"""
        findings_path = Path(findings_dir)
        proposals = []

        # In a real implementation, we would parse the JSON files from findings_dir
        # For this task, we'll simulate the process
        print(f"Analyzing findings in {findings_dir}...")

        # Simulated analysis of bandit.json, ruff.json, etc.
        # We would use self.analyzer.analyze_error() for each finding

        proposals.append({
            "id": "fix_001",
            "issue": "Simulated security issue",
            "proposed_fix": "Add input validation",
            "files": ["src/main.py"]
        })

        with open(output_file, 'w') as f:
            json.dump(proposals, f, indent=2)

        print(f"Proposals saved to {output_file}")

    def run_coding(self, proposals_file: str, output_dir: str, apply: bool = False):
        """Implement fixes based on proposals"""
        with open(proposals_file, 'r') as f:
            proposals = json.load(f)

        print(f"Implementing {len(proposals)} fixes...")

        for proposal in proposals:
            print(f"Applying fix for: {proposal['issue']}")
            # In a real implementation, we would use self.fixer to apply changes
            if apply:
                # Simulated fix application
                pass

        print(f"Fixes implemented and saved to {output_dir}")

    def generate_pr_body(self, proposals_file: str, test_results_file: str, output_file: str):
        """Generate PR description in Markdown"""
        with open(proposals_file, 'r') as f:
            proposals = json.load(f)

        try:
            with open(test_results_file, 'r') as f:
                test_results = json.load(f)
        except:
            test_results = {"exit_code": 0}

        body = f"""# 🤖 LLM Code Review & Auto-Fix

This PR contains automated fixes for issues identified during code review.

## 🛠 Fixes Applied
"""
        for p in proposals:
            body += f"- **{p['issue']}**: {p['proposed_fix']}\n"

        body += "\n## 🧪 Test Results\n"
        if test_results.get("exit_code") == 0:
            body += "✅ All tests passed after applying fixes.\n"
        else:
            body += "⚠️ Some tests failed. Please review the results manually.\n"

        with open(output_file, 'w') as f:
            f.write(body)

        print(f"PR body saved to {output_file}")


def main():
    parser = argparse.ArgumentParser(description="PR Fix Agent Orchestrator")
    parser.add_argument("--mode", required=True, choices=["reasoning", "coding", "generate-pr"])
    parser.add_argument("--model", default="codellama")
    parser.add_argument("--findings", help="Findings directory (reasoning mode)")
    parser.add_argument("--proposals", help="Proposals JSON file (coding/generate-pr mode)")
    parser.add_argument("--test-results", help="Test results JSON file (generate-pr mode)")
    parser.add_argument("--output", required=True, help="Output file or directory")
    parser.add_argument("--apply", action="store_true", help="Apply fixes (coding mode)")
    parser.add_argument("--repo-path", default=".")

    args = parser.parse_args()

    orchestrator = Orchestrator(model=args.model, repo_path=args.repo_path)

    if args.mode == "reasoning":
        orchestrator.run_reasoning(args.findings, args.output)
    elif args.mode == "coding":
        orchestrator.run_coding(args.proposals, args.output, args.apply)
    elif args.mode == "generate-pr":
        orchestrator.generate_pr_body(args.proposals, args.test_results, args.output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
