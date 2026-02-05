class PRErrorAnalyzer:
    # ... (other methods remain the same)

    def parse_github_actions_log(self, log_content: str) -> dict[str, list[str]]:
        """Parse log to extract errors and warnings."""
        errors = []
        for line in log_content.split('\n'):
            for pattern in self.error_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    error = line.strip()
                    # Use a more specific pattern to match typical error messages
                    if 'error' in error.lower() or 'failures' in error.lower():
                        errors.append(error)
                    break
        return {"errors": errors, "warnings": []}

    # ... (other methods remain the same)