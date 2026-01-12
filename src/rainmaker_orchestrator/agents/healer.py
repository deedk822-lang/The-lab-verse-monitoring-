import logging
import os
from typing import Dict, Any

logger = logging.getLogger(__name__)


class SelfHealingAgent:
    """
    Agent responsible for handling alerts and initiating self-healing protocols.
    """

    def __init__(self):
        logger.info("Self-Healing Agent initialized")

    def handle_alert(self, alert_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle alerts from Prometheus Alert Manager.

        Args:
            alert_payload: The alert data from Prometheus

        Returns:
            Status of the healing operation
        """
        logger.info(f"Processing alert: {alert_payload.get('status', 'unknown')}")

        # Extract alert details
        alerts = alert_payload.get("alerts", [])
        if not alerts:
            return {"status": "ignored", "reason": "No alerts in payload"}

        # Basic healing logic: log and acknowledge
        # In a real scenario, this would trigger specific recovery workflows
        return {
            "status": "acknowledged",
            "alert_count": len(alerts),
            "message": "Self-healing protocol initiated",
        }

    def _sanitize_for_prompt(self, text: str, max_length: int = 2000) -> str:
        """Sanitize text for safe inclusion in AI prompts.

        Args:
            text: Raw text input
            max_length: Maximum length before truncation

        Returns:
            Sanitized text safe for prompt injection
        """
        if not text or not isinstance(text, str):
            return "N/A"

        # Remove code block markers that could break prompt structure
        text = text.replace("```", "")

        # Remove null bytes and control characters except newline/tab
        text = text.replace("\x00", "")
        text = ''.join(
            char for char in text
            if ord(char) >= 32 or char in '\n\t'
        )

        # Truncate if too long
        if len(text) > max_length:
            text = text[:max_length] + "... [truncated for safety]"

        return text.strip()


    async def generate_hotfix(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate hotfix blueprint from alert with input sanitization."""

        # Sanitize all external inputs
        service_name = self._sanitize_for_prompt(
            alert_data.get("labels", {}).get("service", "unknown"),
            max_length=100
        )

        error_log = self._sanitize_for_prompt(
            alert_data.get("annotations", {}).get("error_log", "No logs available"),
            max_length=5000
        )

        severity = self._sanitize_for_prompt(
            alert_data.get("labels", {}).get("severity", "unknown"),
            max_length=50
        )

        # Now safe to use in prompt
        prompt = f"""Analyze this production alert and generate a hotfix blueprint.

Service: {service_name}
Severity: {severity}
Error Log:
{error_log}

Generate a hotfix with impact assessment and confidence score."""
