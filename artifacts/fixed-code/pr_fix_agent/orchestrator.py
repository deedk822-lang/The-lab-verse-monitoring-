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
        return FixProposal(
            finding=finding,
            root_cause="Analyzed root cause from analysis",
            fix_approach="Suggested approach based on LLM response",
            expected_changes=["Modify affected code"],
            risk_level="low",
            test_requirements=["Verify with existing tests"]
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
                fixes.append(CodeFix(
                    proposal=proposal,
                    file_path=str(file_path),
                    original_code=original_code,
                    fixed_code=fixed_code,
                    explanation="Automated fix implementation"
                ))
            except Exception as e:
                logger.error("coding_failed", file=proposal.finding.file, error=str(e))
        return fixes

    def _apply_and_test(self, fixes: list[CodeFix], repo_path: Path) -> TestResult:
        """Apply fixes and run tests"""
        for fix in fixes:
            Path(fix.file_path).write_text(fixed_code)
            try:
                process = subprocess.Popen(["./" + fix.original_code], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out, err = process.communicate()
                if process.returncode != 0:
                    logger.error("test_failed", file=fix.file_path, output=out.decode(), error=err.decode())
                    return TestResult(False, len(fix.expected_changes), 0, [], ["Test failed"])
            except Exception as e:
                logger.error("running_test_failed", file=fix.file_path, error=str(e))
                return TestResult(False, len(fix.expected_changes), 0, [], ["Running test failed"])

        logger.info("all_tests_passed")
        return TestResult(True, len(fix.expected_changes), len(fix.expected_changes), [], [])

    def generate_pr_body(self, proposals: list[FixProposal], fixes: list[CodeFix], test_result: TestResult) -> str:
        body = ""
        if not proposals:
            body += "No findings found.\n"
        else:
            body += "Problems found:\n"
            for proposal in proposals:
                body += f"- {proposal.finding.file}:{proposal.finding.line_start}-{proposal.finding.line_end}: {proposal.finding.issue}\n"

        if not fixes:
            body += "\nNo fixes generated.\n"
        else:
            body += "\nFixes generated:\n"
            for fix in fixes:
                body += f"- {fix.file_path}: Fix\n"

        if test_result:
            body += "\nTest results:\n"
            passed = test_result.passed
            failed = len(test_result.expected_changes) - test_result.failed_tests
            total = len(test_result.expected_changes)
            if passed and failed == 0:
                body += f"- All tests passed.\n"
            else:
                body += f"- Passed: {passed}, Failed: {failed}\n"

        return body

    def __enter__(self):
        self.cost_tracker.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.cost_tracker.stop_and_log("Completed successfully.")
        else:
            self.cost_tracker.stop_and_log(f"Failed with error: {exc_val}")

# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    sys.exit(main())