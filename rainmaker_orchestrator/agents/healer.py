import json
import logging
import re
import shlex
from typing import Any, Dict, List

from rainmaker_orchestrator.clients.kimi import KimiClient
from rainmaker_orchestrator.core import RainmakerOrchestrator

logger: logging.Logger = logging.getLogger("healer")


class SelfHealingAgent:
    """Self-healing agent for command injection prevention and code repair.

    This agent receives alert payloads from monitoring systems (e.g., Prometheus)
    and uses AI to analyze errors and generate automated hotfixes.
    """

    MAX_RETRIES: int = 3
    COMMAND_INJECTION_PATTERNS: List[str] = [
        r"[;&|`$()]",  # Shell metacharacters
        r"__import__",  # Python injection
        r"eval\(",  # Dynamic code execution
    ]

    def __init__(self, kimi_client: Any = None, orchestrator: Any = None) -> None:
        """
        Initialize the self-healing agent.

        Args:
            kimi_client: Optional KimiClient instance. If not provided, creates a new one.
            orchestrator: Optional RainmakerOrchestrator instance. If not provided, creates a new one.
        """
        self.kimi_client = kimi_client or self._init_kimi_client()
        self.orchestrator = orchestrator or self._init_orchestrator()
        logger.info("Self-Healing Agent initialized")

    def _init_kimi_client(self) -> KimiClient:
        """
        Initialize a new KimiClient instance.

        Returns:
            KimiClient: A new KimiClient instance
        """
        return KimiClient()

    def _init_orchestrator(self) -> RainmakerOrchestrator:
        """
        Initialize a new RainmakerOrchestrator instance.

        Returns:
            RainmakerOrchestrator: A new orchestrator instance
        """
        from rainmaker_orchestrator.config import ConfigManager
        settings = ConfigManager()
        return RainmakerOrchestrator(workspace_path=str(settings.get("WORKSPACE_PATH", "./workspace")))

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
    def safe_parse_command(command: str) -> List[str]:
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

    def handle_alert(self, alert_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle an incoming alert and generate a hotfix.

        Receives a Prometheus Alert Manager webhook payload, analyzes the error,
        and generates an AI-powered hotfix blueprint.

        Args:
            alert_payload: Dictionary containing alert information:
                - description: Error description or log
                - service: Name of the affected service
                - alerts: List of alerts (optional format)

        Returns:
            Dictionary with status and hotfix information:
            - status: 'hotfix_generated', 'hotfix_failed', 'acknowledged', 'ignored'
            - blueprint: Generated hotfix code (if successful)
            - error: Error message (if failed)
        """
        # Check for multiple alerts in payload
        alerts = alert_payload.get('alerts', [])
        if not alerts and 'description' not in alert_payload and 'service' not in alert_payload:
            return {"status": "ignored", "reason": "No alerts, description or service in payload"}

        error_log = alert_payload.get('description')
        if not error_log:
            error_log = 'No description provided'
        service_name = alert_payload.get('service', 'Unknown service')

        if not alerts:
            # Handle single alert from direct description
            prompt = f"""
            CRITICAL ALERT in service: {service_name}
            Error Log: {error_log}

            Task:
            1. Analyze the error.
            2. Generate a patch file to fix this specific exception.
            3. Do not refactor unrelated code.
            """

            try:
                # Trigger Kimi with "Hotfix" priority
                blueprint = self.kimi_client.generate(prompt, mode="hotfix")

                if blueprint is None:
                    logger.error(f"Failed to generate hotfix for {service_name} due to Kimi client error.")
                    return {"status": "hotfix_failed", "error": "Blueprint generation failed"}

                # In a real implementation, this would involve deploying the hotfix
                logger.info(f"Generated hotfix for {service_name}: {blueprint}")
                return {"status": "hotfix_generated", "blueprint": blueprint}
            except Exception as e:
                logger.exception(f"Exception while handling alert for {service_name}")
                return {"status": "hotfix_failed", "error": str(e)}
        else:
            # Handle multiple alerts (legacy format)
            return {
                "status": "acknowledged",
                "alert_count": len(alerts),
                "message": "Self-healing protocol initiated for multiple alerts"
            }
