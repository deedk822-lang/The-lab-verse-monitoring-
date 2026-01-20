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
        """
        Check a shell command string for patterns commonly associated with command injection.
        
        Parameters:
            command (str): The shell command string to validate.
        
        Returns:
            true if the command contains none of the configured injection patterns, false otherwise.
        """
        for pattern in SelfHealingAgent.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, command):
                logger.warning(f"Potential injection detected: {pattern}")
                return False
        return True

    @staticmethod
    def safe_parse_command(command: str) -> list:
        """
        Parse a shell command into a list of arguments after validating it against injection patterns.
        
        Parameters:
            command (str): The shell command string to validate and parse.
        
        Returns:
            list: The parsed list of command arguments.
        
        Raises:
            ValueError: If the command fails security validation or parsing fails.
        """
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
        """
        Extracts a JSON object from a string that may include Markdown code fences.
        
        Parameters:
            response (str): Input text potentially containing JSON wrapped in triple-backtick Markdown code blocks (e.g., ```json ... ```).
        
        Returns:
            dict: Parsed JSON object.
        
        Raises:
            json.JSONDecodeError: If the cleaned input cannot be parsed as JSON.
        """
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
        """
        Format a user-facing message for a failed retry attempt.
        
        Parameters:
            error (str): Error message or output produced by the failed attempt.
            attempt (int): Zero-based index of the attempt that failed.
        
        Returns:
            str: A message indicating which attempt (1-based) failed, includes the error content, and prompts the user to fix the issue and retry.
        """
        return f"Attempt {attempt + 1} failed:\n{error}\n\nPlease fix and try again."