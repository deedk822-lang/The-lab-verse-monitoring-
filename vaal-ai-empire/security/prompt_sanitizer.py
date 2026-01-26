import re

class PromptSanitizer:
    """Sanitize user inputs before passing to LLMs"""

    DANGEROUS_PATTERNS = [
        r"ignore\s+(previous|all|above)\s+instructions?",
        r"disregard\s+(previous|all|above)",
        r"forget\s+(everything|all|previous)",
        r"system[:：]\s*[^\n]+",
        r"<\|im_start\|>",
        r"<\|im_end\|>",
        r"<\|endoftext\|>",
        r"###?\s*instruction",
        r"you\s+are\s+now",
        r"act\s+as\s+(if|a)",
        r"pretend\s+to\s+be",
        r"role[:：]\s*system",
        # Unicode tricks
        r"[\u200B-\u200D\uFEFF]",  # Zero-width characters
        # Homoglyph attacks
        r"[Α-Ωα-ω]",  # Greek letters that look like Latin
    ]

    @staticmethod
    def sanitize(text: str, max_length: int = 4000) -> str:
        """Enhanced sanitization with structural preservation"""
        if not text:
            return ""

        # Limit length
        text = text[:max_length]

        # Remove dangerous patterns (case-insensitive)
        for pattern in PromptSanitizer.DANGEROUS_PATTERNS:
            text = re.sub(pattern, "[REDACTED]", text, flags=re.IGNORECASE)

        # Remove control characters but preserve newlines/tabs
        text = "".join(
            char for char in text
            if ord(char) >= 32 or char in "\n\t\r"
        )

        # Normalize whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)

        return text.strip()
