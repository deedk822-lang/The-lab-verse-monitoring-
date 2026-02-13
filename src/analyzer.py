class ErrorStatistics:
    """Track and analyze error statistics"""

    def __init__(self):
        self.error_counts = {}
        self.category_counts = {}
        self.severity_counts = {}

    def record_error(self, error: str, category: str, severity: str):
        """Record an error for statistics"""
        # Count by error message
        self.error_counts[error] = self.error_counts.get(error, 0) + 1

        # Count by category
        self.category_counts[category] = self.category_counts.get(category, 0) + 1

        # Count by severity
        self.severity_counts[severity] = self.severity_counts.get(severity, 0) + 1

    def get_most_common_errors(self, top_n: int = 5) -> List[tuple]:
        """Get most common errors"""
        sorted_errors = sorted(
            self.error_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_errors[:top_n]

    def get_summary(self) -> Dict:
        """Get summary statistics"""
        return {
            "total_errors": sum(self.error_counts.values()),
            "unique_errors": len(self.error_counts),
            "by_category": self.category_counts,
            "by_severity": self.severity_counts,
            "most_common": self.get_most_common_errors()
        }

    def get_error_context(
        self, log_content: str, error_line: str, context_lines: int = 3
    ) -> list[str]:
        """Get context lines around an error"""
        if not isinstance(log_content, str) or not isinstance(error_line, str):
            raise ValueError("Both log_content and error_line must be strings")

        try:
            lines = log_content.split("\n")
            error_index = lines.index(error_line)
            start = max(0, error_index - context_lines)
            end = min(len(lines), error_index + context_lines + 1)
            return lines[start:end]
        except ValueError:
            return []