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

            # Load json report if it exists
            report_path = repo_path / "test-results.json"
            total = 0
            passed_count = 0
            failed_count = 0
            if report_path.exists():
                with open(report_path) as f:
                    data = json.load(f)
                    summary = data.get('summary', {})
                    passed_count = summary.get('passed', 0)
                    failed_count = summary.get('failed', 0)
                    total = summary.get('total', passed_count + failed_count)

            return TestResult(
                passed=(result.returncode == 0),
                total_tests=total,
                passed_tests=passed_count,
                failed_tests=failed_count,
                exit_code=result.returncode,
                output=result.stdout + "\n" + result.stderr,
                failures=[]
            )
        except Exception as e:
            logger.error("test_execution_failed", error=str(e))
            return TestResult(False, 0, 0, 0, 1, str(e), [str(e)])

    def generate_pr_body(self, proposals: List[FixProposal], fixes: List[CodeFix], test_result: Optional[TestResult]) -> str:
        body = "# 🤖 Automated Code Review Fixes\n\n"

        if test_result:
            body += f"Tests: {'✅ PASSED' if test_result.passed else '❌ FAILED'}\n"
            body += f"- Total: {test_result.total_tests}\n"
            body += f"- Passed: {test_result.passed_tests}\n"
            body += f"- Failed: {test_result.failed_tests}\n"
            body += f"Exit Code: {test_result.exit_code}\n"
            body += f"Output: {test_result.output}\n"
            body += f"Failures: {', '.join(test_result.failures)}\n"
        else:
            body += f"No tests performed.\n"

        for p in proposals:
            body += f"Proposed Fix:\n- File: {p.finding.file}\n- Issue: {p.finding.issue}\n"
            body += f"- Suggestion: {p.fix_approach}\n"
            body += f"- Expected Changes: {', '.join(p.expected_changes)}\n"

        for f in fixes:
            body += f"Implemented Fix:\n- File: {f.file_path}\n- Original Code:\n{f.original_code}\n"
            body += f"- Fixed Code:\n{f.fixed_code}\n"
            body += f"- Explanation: {f.explanation}\n"

        return body

if __name__ == "__main__":
    sys.exit(main())