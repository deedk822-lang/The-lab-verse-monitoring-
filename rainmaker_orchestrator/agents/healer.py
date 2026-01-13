import logging
import re
import json
import shlex
from typing import Dict, Any, Optional

logger: logging.Logger = logging.getLogger("healer")


class SelfHealingAgent:
    """Self-healing agent for command injection prevention and code repair."""

    MAX_RETRIES: int = 3
    COMMAND_INJECTION_PATTERNS: list = [
        r"[;&|`$()]",  # Shell metacharacters
        r"__import__",  # Python injection
        r"eval\(",  # Dynamic code execution
    ]

    @staticmethod
    def validate_command(command: str) -> bool:
        """Validate command for injection patterns."""
        for pattern in SelfHealingAgent.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, command):
                logger.warning(f"Potential injection detected: {pattern}")
                return False
        return True

    @staticmethod
    def safe_parse_command(command: str) -> list:
        """Safely parse shell commands using shlex."""
        try:
            if not SelfHealingAgent.validate_command(command):
                raise ValueError("Command failed security validation")
            parsed: list = shlex.split(command)
            logger.info(f"Command parsed safely: {len(parsed)} args")
            return parsed
        except ValueError as e:
            logger.error(f"Command parsing failed: {str(e)}")
            raise

    @staticmethod
    def extract_json(response: str) -> Dict[str, Any]:
        """Extract and validate JSON from LLM response."""
        try:
            # Remove markdown code blocks if present
            clean: str = re.sub(r"^```(?:json)?\s*|\s*```$", "", response.strip(), flags=re.MULTILINE)
            parsed: Dict[str, Any] = json.loads(clean)
            logger.debug("JSON extraction successful")
            return parsed
        except json.JSONDecodeError as e:
            logger.error(f"JSON extraction failed: {str(e)}")
            raise

    @staticmethod
    def format_error_feedback(error: str, attempt: int) -> str:
        """Format error feedback for retry loop."""
        return f"Attempt {attempt + 1} failed:\n{error}\n\nPlease fix and try again."
