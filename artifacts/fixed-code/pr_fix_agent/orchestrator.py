# ...
    def _implement_fixes(self, proposals: List[FixProposal], repo_path: Path) -> List[CodeFix]:
        """Use coding model to implement fixes"""
        fixes = []
        for proposal in proposals:
            prompt = self._create_coding_prompt(proposal)
            try:
                fix = self.coding_agent.query(prompt, temperature=0.1)
                code_fix = self._parse_coding_response(finding, proposal, fix)
                fixes.append(code_fix)
            except Exception as e:
                logger.error("coding_failed", file=finding.file, error=str(e))
        return fixes

    def _create_coding_prompt(self, finding: CodeReviewFinding) -> str:
        prompt = f"""Implement the following code fix proposed by reasoning model.
File: {finding.file}
Finding: {finding.issue}
Suggestion: {finding.suggestion}
Snippet: {finding.code_snippet}
"""
        return prompt

    def _parse_coding_response(self, finding: CodeReviewFinding, proposal: FixProposal, fix: str) -> CodeFix:
        # Simple extraction logic
        return CodeFix(
            proposal=proposal,
            file_path=finding.file,
            original_code=self._get_original_code(repo_path, finding.file),
            fixed_code=fix,
            explanation="Implemented fix based on code response"
        )

    def _get_original_code(self, repo_path: Path, file_name: str) -> str:
        # Simple logic to read the original code from a file
        with open(repo_path / file_name, 'r') as file:
            return file.read()