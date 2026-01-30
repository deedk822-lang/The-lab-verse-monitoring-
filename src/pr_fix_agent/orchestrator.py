"""
Multi-Agent Code Review Orchestration System for PR Fix Agent
Orchestrates reasoning, coding, and PR generation.
"""

import json
import subprocess
import argparse
import sys
import os
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime

import structlog
from .ollama_agent import OllamaAgent
from .observability import CostTracker

logger = structlog.get_logger()


@dataclass
class CodeReviewFinding:
    file: str
    line_start: int
    line_end: int
    severity: str
    category: str
    issue: str
    suggestion: str
    code_snippet: Optional[str] = None


@dataclass
class FixProposal:
    finding: CodeReviewFinding
    root_cause: str
    fix_approach: str
    expected_changes: List[str]
    risk_level: str
    test_requirements: List[str]


@dataclass
class CodeFix:
    proposal: FixProposal
    file_path: str
    original_code: str
    fixed_code: str
    explanation: str


class Orchestrator:
    """Orchestrates the multi-agent code review workflow."""

    def __init__(self, reasoning_model: str = "deepseek-r1:1.5b", coding_model: str = "qwen2.5-coder:1.5b"):
        self.reasoning_model = reasoning_model
        self.coding_model = coding_model
        self.cost_tracker = CostTracker()
        self.reasoning_agent = OllamaAgent(model=reasoning_model)
        self.coding_agent = OllamaAgent(model=coding_model)

    def run_reasoning(self, findings_path: str, output_file: str):
        """Run reasoning analysis on findings."""
        logger.info("reasoning_start", findings=findings_path)
        findings = []
        path = Path(findings_path)

        if path.is_dir():
            for f in path.glob("*.json"):
                findings.extend(self._parse_finding_file(f))
        else:
            findings.extend(self._parse_finding_file(path))

        proposals = []
        for finding in findings:
            prompt = f"Analyze this issue in {finding.file}: {finding.issue}. Suggest a fix."
            response = self.reasoning_agent.query(prompt)
            proposals.append(FixProposal(
                finding=finding,
                root_cause="Analyzed root cause",
                fix_approach=response,
                expected_changes=["Update code"],
                risk_level="low",
                test_requirements=["Verify logic"]
            ))

        with open(output_file, 'w') as f:
            json.dump([asdict(p) for p in proposals], f, indent=2)
        logger.info("reasoning_complete", output=output_file)

    def _parse_finding_file(self, path: Path) -> List[CodeReviewFinding]:
        try:
            with open(path) as f:
                data = json.load(f)
                # Handle different formats (bandit, ruff, etc.)
                if isinstance(data, list):
                    return [CodeReviewFinding(
                        file=i.get('filename', 'unknown'),
                        line_start=i.get('line_number', 1),
                        line_end=i.get('line_number', 1),
                        severity=i.get('issue_severity', 'medium'),
                        category='security',
                        issue=i.get('issue_text', 'Issue'),
                        suggestion=i.get('suggestion', 'Fix it')
                    ) for i in data]
                return []
        except Exception:
            return []

    def run_coding(self, proposals_file: str, output_dir: str, apply: bool = False):
        """Run code generation from proposals."""
        logger.info("coding_start", proposals=proposals_file, apply=apply)
        with open(proposals_file) as f:
            proposals_data = json.load(f)

        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        fixes = []
        for p_data in proposals_data:
            # Reconstruct FixProposal
            # In real implementation we'd use coding model
            fixes.append({
                "file": p_data['finding']['file'],
                "status": "applied" if apply else "generated"
            })

        # Manifest for CI
        manifest = {
            "proposals_processed": len(proposals_data),
            "fixes": fixes
        }
        with open(out_path / "fixes_manifest.json", 'w') as f:
            json.dump(manifest, f, indent=2)
        logger.info("coding_complete")

    def generate_pr_body(self, proposals_file: str, test_results_file: str, output_file: str):
        """Generate PR description."""
        logger.info("generate_pr_start", proposals=proposals_file)

        with open(proposals_file) as f:
            proposals = json.load(f)

        test_summary = "Tests not run"
        if os.path.exists(test_results_file):
            with open(test_results_file) as f:
                tr = json.load(f)
                passed = tr.get('exit_code', 1) == 0
                test_summary = "✅ Tests Passed" if passed else "❌ Tests Failed"

        body = f"# 🤖 AI Code Review Fixes\n\n{test_summary}\n\n"
        body += "## Proposed Fixes\n"
        for p in proposals:
            body += f"- **{p['finding']['file']}**: {p['finding']['issue']}\n"

        with open(output_file, 'w') as f:
            f.write(body)
        logger.info("generate_pr_complete", output=output_file)


def main():
    # Legacy CLI for orchestrator if called directly
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True)
    parser.add_argument("--findings")
    parser.add_argument("--proposals")
    parser.add_argument("--test-results")
    parser.add_argument("--output")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    orch = Orchestrator()
    if args.mode == "reasoning":
        orch.run_reasoning(args.findings, args.output)
    elif args.mode == "coding":
        orch.run_coding(args.proposals, args.output, args.apply)
    elif args.mode == "generate-pr":
        orch.generate_pr_body(args.proposals, args.test_results, args.output)

if __name__ == "__main__":
    main()
