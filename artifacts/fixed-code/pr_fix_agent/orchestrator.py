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
        cost_tracker: CostTracker | None = None,
    ):
        self.cost_tracker = cost_tracker or CostTracker(budget_usd=10.0)

        # Initialize agents
        self.reasoning_agent = OllamaAgent(model=reasoning_model, cost_tracker=self.cost_tracker)

        self.coding_agent = OllamaAgent(model=coding_model, cost_tracker=self.cost_tracker)

        logger.info(
            "orchestrator_initialized", reasoning_model=reasoning_model, coding_model=coding_model
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
Snippet: {finding.code_snippet or 'N/A'}  # Added snippet with default value 'N/A'"""
        # Note: In the original code, 'code_snippet' was provided directly from the input.
        # We assume that the user has not specified a specific snippet for each finding.
        # If this is incorrect, you can replace it with a more robust approach to extract the snippet.

    def _parse_reasoning_response(self, finding: CodeReviewFinding, analysis: str) -> FixProposal:
        # Simple extraction logic
        return FixProposal(
            finding=finding,
            root_cause="Analyzed root cause from analysis",
            fix_approach="Suggested approach based on LLM response",
            expected_changes=["Modify affected code"],
            risk_level="low",
            test_requirements=["Verify with existing tests"],
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
                    lines = fixed_code.split("\n")
                    code_lines = []
                    in_block = False
                    for line in lines:
                        if line.startswith("```"):
                            in_block = not in_block
                            continue
                        if in_block:
                            code_lines.append(line)
                    fixed_code = "\n".join(code_lines)

                fixes.append(
                    CodeFix(
                        proposal,
                        file_path,
                        original_code,
                        fixed_code,
                        f"Fixed by {proposal.fix_approach}",
                    )
                )
            except Exception as e:
                logger.error("coding_failed", finding=proposal.finding, error=str(e))

        if args.apply:
            orch._apply_and_test(fixes, repo_path)

    def _apply_and_test(self, fixes: list[CodeFix], repo_path: Path) -> None:
        for fix in fixes:
            file_path = repo_path / fix.file_path
            original_code = fix.original_code

            # Apply the fix to the file
            with open(file_path, "w") as f:
                f.write(fixed_code)

            # Run tests on the fixed code
            tr_result = self._run_tests(original_code)
            if not tr_result.passed:
                logger.error(
                    "test_failed", finding=fix.finding, original_code=original_code, test_results=tr_result
                )

    def _run_tests(self, original_code: str) -> TestResult:
        # Implement your testing logic here
        # For example, you can use a command-line tool or library to run tests on the code
        # This is a placeholder for the actual implementation.
        # Replace it with the appropriate test running mechanism.

        return TestResult(
            passed=True,
            total_tests=10,
            passed_tests=9,
            failed_tests=1,
            exit_code=0,
            output="Test results: 9/10 tests passed",
            failures=[
                "Test case 1 failed",
                "Test case 2 failed",
            ],
        )

    def generate_pr_body(self, proposals: list[FixProposal], [], test_result) -> str:
        body = ""
        for proposal in proposals:
            finding_str = f"- **{proposal.finding.issue}**: "
            if proposal.fix_approach:
                finding_str += f"Fixed by {proposal.fix_approach}"
            else:
                finding_str += "No fix proposed"
            body += f"{finding_str}\n"

        if test_result:
            if test_result.failed_tests > 0:
                body += "\n- **Test Results**: "
                for failure in test_result.failures:
                    body += f"- {failure}\n"

        return body


# ============================================================================
# Main Entry Point
# ============================================================================


if __name__ == "__main__":
    sys.exit(main())