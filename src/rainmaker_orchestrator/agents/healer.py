import logging
import re
from typing import Dict, Any, Optional

# Assuming a shared KimiApiClient is available, otherwise it needs to be imported and instantiated.
# from ..clients.kimi import KimiApiClient

# A mock client for demonstration if the actual client is not available.
class MockKimiApiClient:
    async def generate_chat_completion(self, messages: list) -> str:
        # Simulate a response for testing purposes
        return '{"hotfix": "This is a simulated hotfix.", "confidence": 0.9, "impact": "low"}'

logger = logging.getLogger(__name__)

class SelfHealingAgent:
    """
    Agent responsible for handling alerts and initiating self-healing protocols.
    """
    def __init__(self, kimi_client=None):
        logger.info("Self-Healing Agent initialized")
        # In a real application, the KimiApiClient would be injected.
        self.kimi_client = kimi_client or MockKimiApiClient()

    def _sanitize_for_prompt(
        self,
        text: str,
        max_length: int = 2000,
        field_name: str = "input"
    ) -> str:
        """Sanitize text for safe LLM prompt inclusion."""
        if not text or not isinstance(text, str):
            logger.warning(f"invalid_{field_name}_type", type=type(text))
            return "N/A"

        text = text.replace("```", "").replace("'''", "")
        text = text.replace("\x00", "")
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')

        injection_patterns = [
            r"ignore\s+previous\s+instructions",
            r"system\s*:\s*you\s+are",
            r"<\s*script",
        ]
        for pattern in injection_patterns:
            text = re.sub(pattern, "[REDACTED]", text, flags=re.IGNORECASE)

        if len(text) > max_length:
            logger.info(
                f"{field_name}_truncated",
                original_length=len(text),
                truncated_length=max_length
            )
            text = text[:max_length] + "... [truncated for safety]"

        return text.strip()

    async def generate_hotfix(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate hotfix with input sanitization."""
        service_name = self._sanitize_for_prompt(
            alert_data.get("labels", {}).get("service", "unknown"),
            max_length=100,
            field_name="service_name"
        )

        error_log = self._sanitize_for_prompt(
            alert_data.get("annotations", {}).get("error_log", ""),
            max_length=5000,
            field_name="error_log"
        )

        prompt = f"""Analyze this production alert and generate a hotfix.

Service: {service_name}
Error Log:
{error_log}

Generate a hotfix with confidence score and impact assessment."""

        response = await self.kimi_client.generate_chat_completion(
            messages=[
                {"role": "system", "content": "You are a production incident response expert."},
                {"role": "user", "content": prompt}
            ]
        )

        return {"hotfix": response, "service": service_name}

    async def handle_alert(self, alert_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle alerts from Prometheus Alert Manager and generate a hotfix for each.
        """
        status = alert_payload.get('status', 'unknown')
        logger.info("Processing alert", extra={"status": status})

        alerts = alert_payload.get('alerts', [])
        if not alerts:
            return {"status": "ignored", "reason": "No alerts in payload"}

        hotfix_responses = []
        for alert in alerts:
            hotfix_response = await self.generate_hotfix(alert)
            hotfix_responses.append(hotfix_response)

        return {
            "status": "healing_initiated",
            "alert_count": len(alerts),
            "hotfixes": hotfix_responses
        }
