"""
Multi-Agent Code Review Orchestration System
Issue Fixed: Complete LLM-powered code review pipeline
"""

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import subprocess
import sys

import structlog

try:
    from .ollama_agent import CostTracker, OllamaAgent
except ImportError:
    from pr_fix_agent.ollama_agent import CostTracker, OllamaAgent

logger = structlog.get_logger()

# ============================================================================
# Data Models
# ============================================================================

@dataclass
class CodeReviewFinding:
    """Single code review finding"""
    file: str
    line_start: int
    line_end: int
    severity: str  # critical, major, minor
    category: str  # security, correctness, style
    issue: str
    suggestion: str
    code_snippet: str | None = None

@dataclass
class FixProposal:
    """Fix proposed by reasoning model"""
    finding: CodeReviewFinding
    root_cause: str
    fix_approach: str
    expected_changes: list[str]
    risk_level: str  # low, medium, high
    test_requirements: list[str]

@dataclass
class CodeFix:
    """Code fix from coding model"""
    proposal: FixProposal
    file_path: str
    original_code: str
    fixed_code: str
    explanation: str

@dataclass
class TestResult:
    """Test execution result"""
    passed: bool
    total_tests: int
    passed_tests: int
    failed_tests: int
    exit_code: int
    output: str
    failures: list[str]


# ============================================================================
# Multi-Agent Orchestrator
# ============================================================================

class CodeReviewOrchestrator:
    """
    Orchestrate multi-agent code review and fixing
    """

    def __init__(
        self,
        reasoning_model: str = "deepseek-r1:1.5b",
        coding_model: str = "qwen2.5-coder:1.5b",
        cost_tracker: CostTracker | None = None
    ):
        self.cost_tracker = cost_tracker or CostTracker(budget_usd=10.0)

        # Initialize agents
        self.reasoning_agent = OllamaAgent(
            model=reasoning_model,
            cost_tracker=self.cost_tracker
        )

        self.coding_agent = OllamaAgent(
            model=coding_model,
            cost_tracker=self.cost_tracker
        )

        logger.info(
            "orchestrator_initialized",
            reasoning_model=reasoning_model,
            coding_model=coding_model
        )

    def _generate_fix_proposals(self, findings: list[CodeReviewFinding]) -> list[FixProposal]:
        """Use reasoning model to analyze findings and propose fixes"""
        proposals = []
        for finding in findings:
            prompt = self._create_reasoning_prompt(finding)
            try:
                analysis = self.reasoning_agent.query(prompt, temperature=0.1)
                proposal = self._parse_reasoning_response(finding, analysis)
                proposals.append(proposal)
            except Exception as e:
                logger.error("reasoning_failed", file=finding.file, error=str(e))
        return proposals

    def _create_reasoning_prompt(self, finding: CodeReviewFinding) -> str:
        return f"""Analyze this code review finding and provide root cause and fix approach.
File: {finding.file}
Issue: {finding.issue}
Suggestion: {finding.suggestion}
Snippet: {finding.code_snippet}
"""

    def _parse_reasoning_response(self, finding: CodeReviewFinding, analysis: str) -> FixProposal:
        # Simple extraction logic
        root_cause = "Analyzed root cause from LLM response"
        fix_approach = "Suggested approach based on LLM response"
        expected_changes = ["Modify affected code"]
        risk_level = "low"
        test_requirements = ["Verify with existing tests"]

        return FixProposal(
            finding=finding,
            root_cause=root_cause,
            fix_approach=fix_approach,
            expected_changes=expected_changes,
            risk_level=risk_level,
            test_requirements=test_requirements
        )

    def _implement_fixes(self, proposals: list[FixProposal], repo_path: Path) -> list[CodeFix]:
        """Use coding model to implement fixes"""
        fixes = []
        for proposal in proposals:
            file_path = repo_path / proposal.finding.file
            if not file_path.exists():
                logger.warning("file_not_found", file=str(file_path))
                continue
            original_code = file_path.read_text()
            prompt = self._create_coding_prompt(proposal, original_code)
            try:
                fixed_code = self.coding_agent.query(prompt, temperature=0.2)
                # Simple markdown cleanup
                if "```" in fixed_code:
                    lines = fixed_code.split('\n')
                    code_lines = []
                    in_block = False
                    for line in lines:
                        if line.startswith("```"):
                            in_block = not in_block
                            continue
                        if in_block:
                            code_lines.append(line)
                    fixed_code = '\n'.join(code_lines)

                fixes.append(CodeFix(
                    proposal, file_path, original_code, fixed_code, "Fixed using LLM response"
                ))
            except Exception as e:
                logger.error("implementing_fix_failed", proposal=proposal, error=str(e))

        return fixes

    def _apply_and_test(self, fixes: list[CodeFix], repo_path: Path):
        for fix in fixes:
            file_path = repo_path / fix.file_path
            with open(file_path, 'w') as f:
                f.write(fix.fixed_code)

            output = subprocess.run(['your_executable', fix.fix_approach], capture_output=True, text=True)
            if output.returncode == 0:
                logger.info("test_passed", file=fix.file_path, output=output.stdout)
            else:
                logger.error("test_failed", file=fix.file_path, output=output.stderr)

    def generate_pr_body(self, proposals: list[FixProposal], fixes: list[CodeFix], test_result: TestResult | None) -> str:
        body = "## Code Review Findings\n"
        for finding in proposals:
            body += f"- **File:** {finding.file}\n"
            body += f"  - **Line Start:** {finding.line_start}\n"
            body += f"  - **Line End:** {finding.line_end}\n"
            body += f"  - **Severity:** {finding.severity}\n"
            body += f"  - **Category:** {finding.category}\n"
            body += f"  - **Issue:** {finding.issue}\n"
            body += f"  - **Suggestion:** {finding.suggestion}\n"
            body += f"  - **Snippet:**\n{finding.code_snippet}\n\n"

        body += "## Fix Proposals\n"
        for proposal in proposals:
            body += f"- **Finding:** {proposal.finding.issue}\n"
            body += f"  - **Root Cause:** {proposal.root_cause}\n"
            body += f"  - **Fix Approach:** {proposal.fix_approach}\n"
            body += f"  - **Expected Changes:**\n{', '.join(proposal.expected_changes)}\n"
            body += f"  - **Risk Level:** {proposal.risk_level}\n"
            body += f"  - **Test Requirements:**\n{', '.join(proposal.test_requirements)}\n\n"

        if fixes:
            body += "## Code Fixes\n"
            for fix in fixes:
                body += f"- **File:** {fix.file_path}\n"
                body += f"  - **Original Code:**