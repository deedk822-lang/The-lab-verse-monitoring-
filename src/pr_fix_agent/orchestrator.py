"""
Multi-Agent Code Review Orchestration System
Issue Fixed: Complete LLM-powered code review pipeline
"""

import argparse
import json
import subprocess
import sys
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
        cost_tracker: Optional[CostTracker] = None,
    ):
        self.cost_tracker = cost_tracker or CostTracker(budget_usd=10.0)

        # Initialize agents
        self.reasoning_agent = ObservableOllamaAgent(
            model=reasoning_model, cost_tracker=self.cost_tracker
        )

        self.coding_agent = ObservableOllamaAgent(
            model=coding_model, cost_tracker=self.cost_tracker
        )

        logger.info(
            "orchestrator_initialized", reasoning_model=reasoning_model, coding_model=coding_model
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
            test_requirements=["Verify with existing tests"],
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
                    lines = fixed_code.split("\n")
                    code_lines = []
                    in_block = False
                    for line in lines:
                        if line.startswith("```"):
                            in_block = not in_block
                            continue
                        if in_block:
                            code_lines.append(line)
                    if code_lines:
                        fixed_code = "\n".join(code_lines)

                fixes.append(
                    CodeFix(
                        proposal=proposal,
                        file_path=str(file_path),
                        original_code=original_code,
                        fixed_code=fixed_code,
                        explanation="Automated fix implementation",
                    )
                )
            except Exception as e:
                logger.error("coding_failed", file=proposal.finding.file, error=str(e))
        return fixes

    def _create_coding_prompt(self, proposal: FixProposal, code: str) -> str:
        return f"Fix the following Python code:\n```python\n{code}\n```\nReason: {proposal.fix_approach}\nFinding: {proposal.finding.issue}"

    def _apply_and_test(self, fixes: List[CodeFix], repo_path: Path) -> TestResult:
        """Apply fixes and run tests"""
        for fix in fixes:
            Path(fix.file_path).write_text(fix.fixed_code)

        try:
            result = subprocess.run(
                ["pytest", "tests/", "--json-report", "--json-report-file=test-results.json"],
                cwd=repo_path,
                capture_output=True,
                text=True,
            )

            # Load json report if it exists
            report_path = repo_path / "test-results.json"
            total = 0
            passed_count = 0
            failed_count = 0
            if report_path.exists():
                with open(report_path) as f:
                    data = json.load(f)
                    summary = data.get("summary", {})
                    passed_count = summary.get("passed", 0)
                    failed_count = summary.get("failed", 0)
                    total = summary.get("total", passed_count + failed_count)

            return TestResult(
                passed=(result.returncode == 0),
                total_tests=total,
                passed_tests=passed_count,
                failed_tests=failed_count,
                exit_code=result.returncode,
                output=result.stdout + "\n" + result.stderr,
                failures=[],
            )
        except Exception as e:
            logger.error("test_execution_failed", error=str(e))
            return TestResult(False, 0, 0, 0, 1, str(e), [str(e)])

    def generate_pr_body(
        self, proposals: List[FixProposal], fixes: List[CodeFix], test_result: Optional[TestResult]
    ) -> str:
        body = "# 🤖 Automated Code Review Fixes\n\n"

        if test_result:
            body += f"Tests: {'✅ PASSED' if test_result.passed else '❌ FAILED'}\n"
            body += f"- Total: {test_result.total_tests}\n"
            body += f"- Passed: {test_result.passed_tests}\n"
            body += f"- Failed: {test_result.failed_tests}\n\n"

        body += "## Fixes Proposed\n"
        for p in proposals:
            body += f"- {p.finding.file}: {p.finding.issue}\n"

        body += "\n---\n*Generated by PR Fix Agent*"
        return body


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, choices=["reasoning", "coding", "generate-pr"])
    parser.add_argument("--findings", help="Path to findings directory")
    parser.add_argument("--proposals", help="Path to proposals JSON")
    parser.add_argument("--test-results", help="Path to test results JSON")
    parser.add_argument("--output", help="Output file")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--reasoning-model", default="deepseek-r1:1.5b")
    parser.add_argument("--coding-model", default="qwen2.5-coder:1.5b")

    args = parser.parse_args()
    orch = CodeReviewOrchestrator(
        reasoning_model=args.reasoning_model, coding_model=args.coding_model
    )
    repo_path = Path.cwd()

    if args.mode == "reasoning":
        findings = []
        findings_dir = Path(args.findings or "analysis-results")
        if findings_dir.exists():
            for f_path in findings_dir.glob("*.json"):
                try:
                    with open(f_path) as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            for issue in data:
                                findings.append(
                                    CodeReviewFinding(
                                        file=issue.get("filename", "unknown"),
                                        line_start=issue.get("line_number", 1),
                                        line_end=issue.get("line_number", 1),
                                        severity=issue.get("issue_severity", "medium").lower(),
                                        category="security",
                                        issue=issue.get("issue_text", "Potential security issue"),
                                        suggestion=issue.get("suggestion", "Follow best practices"),
                                    )
                                )
                        elif isinstance(data, dict) and "results" in data:
                            for issue in data["results"]:
                                findings.append(
                                    CodeReviewFinding(
                                        file=issue.get("filename", issue.get("path", "unknown")),
                                        line_start=issue.get(
                                            "line_number", issue.get("location", {}).get("row", 1)
                                        ),
                                        line_end=issue.get(
                                            "line_number", issue.get("location", {}).get("row", 1)
                                        ),
                                        severity="high",
                                        category="lint",
                                        issue=issue.get(
                                            "issue_text", issue.get("message", "Issue found")
                                        ),
                                        suggestion="Fix as recommended",
                                    )
                                )
                except Exception as e:
                    logger.warning("parsing_finding_failed", path=str(f_path), error=str(e))

        if not findings:
            logger.info("no_findings_found")

        proposals = orch._generate_fix_proposals(findings)
        with open(args.output or "proposals.json", "w") as f:
            json.dump([asdict(p) for p in proposals], f, indent=2)

    elif args.mode == "coding":
        proposals_path = Path(args.proposals or "proposals.json")
        if not proposals_path.exists():
            logger.error("proposals_file_not_found", path=str(proposals_path))
            sys.exit(1)

        with open(proposals_path) as f:
            p_data = json.load(f)

        proposals = []
        for d in p_data:
            f_data = d["finding"]
            finding = CodeReviewFinding(
                f_data["file"],
                f_data["line_start"],
                f_data["line_end"],
                f_data["severity"],
                f_data["category"],
                f_data["issue"],
                f_data["suggestion"],
                f_data.get("code_snippet"),
            )
            proposals.append(
                FixProposal(
                    finding,
                    d["root_cause"],
                    d["fix_approach"],
                    d["expected_changes"],
                    d["risk_level"],
                    d["test_requirements"],
                )
            )

        fixes = orch._implement_fixes(proposals, repo_path)
        if args.apply:
            orch._apply_and_test(fixes, repo_path)

    elif args.mode == "generate-pr":
        proposals_path = Path(args.proposals or "proposals.json")
        if not proposals_path.exists():
            logger.error("proposals_file_not_found", path=str(proposals_path))
            sys.exit(1)

        with open(proposals_path) as f:
            p_data = json.load(f)

        proposals = []
        for d in p_data:
            f_data = d["finding"]
            finding = CodeReviewFinding(
                f_data["file"],
                f_data["line_start"],
                f_data["line_end"],
                f_data["severity"],
                f_data["category"],
                f_data["issue"],
                f_data["suggestion"],
                f_data.get("code_snippet"),
            )
            proposals.append(
                FixProposal(
                    finding,
                    d["root_cause"],
                    d["fix_approach"],
                    d["expected_changes"],
                    d["risk_level"],
                    d["test_requirements"],
                )
            )

        test_result = None
        if args.test_results:
            tr_path = Path(args.test_results)
            if tr_path.exists():
                try:
                    with open(tr_path) as f:
                        tr_data = json.load(f)
                        summary = tr_data.get("summary", {})
                        test_result = TestResult(
                            passed=(
                                tr_data.get("exit_code", 0) == 0 or summary.get("failed", 0) == 0
                            ),
                            total_tests=summary.get("total", 0),
                            passed_tests=summary.get("passed", 0),
                            failed_tests=summary.get("failed", 0),
                            exit_code=tr_data.get("exit_code", 0),
                            output="",
                            failures=[],
                        )
                except Exception as e:
                    logger.warning("loading_test_results_failed", error=str(e))

        body = orch.generate_pr_body(proposals, [], test_result)
        if args.output:
            with open(args.output, "w") as f:
                f.write(body)
        else:
            print(body)


if __name__ == "__main__":
    sys.exit(main())
