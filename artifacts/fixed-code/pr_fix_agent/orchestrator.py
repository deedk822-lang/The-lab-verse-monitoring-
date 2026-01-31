from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional

import structlog

from pr_fix_agent.observability import ObservableOllamaAgent
from pr_fix_agent.ollama_agent import CostTracker

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
    code_snippet: Optional[str] = None


@dataclass
class FixProposal:
    """Fix proposed by reasoning model"""
    finding: CodeReviewFinding
    root_cause: str
    fix_approach: str
    expected_changes: List[str]
    risk_level: str  # low, medium, high
    test_requirements: List[str]


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
    failures: List[str]


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
        cost_tracker: Optional[CostTracker] = None
    ):
        self.cost_tracker = cost_tracker or CostTracker(budget_usd=10.0)

        # Initialize agents
        self.reasoning_agent = ObservableOllamaAgent(
            model=reasoning_model,
            cost_tracker=self.cost_tracker
        )

        self.coding_agent = ObservableOllamaAgent(
            model=coding_model,
            cost_tracker=self.cost_tracker
        )

        logger.info(
            "orchestrator_initialized",
            reasoning_model=reasoning_model,
            coding_model=coding_model
        )

    def _generate_fix_proposals(self, findings: List[CodeReviewFinding]) -> List[FixProposal]:
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

    def _implement_fixes(self, proposals: List[FixProposal], repo_path: Path) -> List[CodeFix]:
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
                    if code_lines:
                        fixed_code = '\n'.join(code_lines)

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

    def _apply_and_test(self, fixes: List[CodeFix], repo_path: Path) -> TestResult:
        """Apply fixes and run tests"""
        for fix in fixes:
            Path(fix.file_path).write_text(fix.fixed_code)

        try:
            result = subprocess.run(
                ["pytest", "tests/", "--json-report", "--json-report-file=test-results.json"],
                cwd=repo_path, capture_output=True, text=True
            )

            # Load json report file
            tr_data = {}
            if result.stdout:
                try:
                    tr_data = json.loads(result.stdout)
                except Exception as e:
                    logger.warning("loading_json_report_failed", error=str(e))

            summary = tr_data.get('summary', {})
            test_result = TestResult(
                passed=(tr_data.get('exit_code', 0) == 0 or summary.get('failed', 0) == 0),
                total_tests=summary.get('total', 0),
                passed_tests=summary.get('passed', 0),
                failed_tests=summary.get('failed', 0),
                exit_code=result.returncode,
                output=result.stdout,
                failures=tr_data.get('failures', [])
            )

        except Exception as e:
            logger.warning("applying_and_testing_failed", error=str(e))

        return test_result

    def generate_pr_body(self, proposals: List[FixProposal], fixes: List[CodeFix], test_result: Optional[TestResult] = None) -> str:
        body = f"## Code Review Findings\n\n"
        for p in proposals:
            body += f"- **File:** `{p.finding.file}`\n- **Issue:** {p.finding.issue}\n- **Suggestion:** {p.fix_approach}\n\n"

        if fixes:
            body += "## Fix Proposals\n\n"
            for f in fixes:
                body += f"- **File:** `{f.file_path}`\n- **Original Code:** {f.original_code[:50]}...\n- **Fixed Code:** {f.fixed_code[:50]}...\n- **Explanation:** {f.explanation}\n\n"

        if test_result and test_result.passed:
            body += "## Test Results\n\n### Passed Tests\n\n"
            for i, f in enumerate(test_result.failures):
                body += f"- **Test {i+1}:** {f}\n\n"
        else:
            body += "## Test Results\n\n### Failed Tests\n\n"
            for f in test_result.failures:
                body += f"- **Test:** {f}\n\n"

        return body


# ============================================================================
# Main Function
# ============================================================================

if __name__ == "__main__":
    sys.exit(main())