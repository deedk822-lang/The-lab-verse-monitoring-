import logging
import os
from typing import Dict, Any
from rainmaker_orchestrator.core import RainmakerOrchestrator
from rainmaker_orchestrator.clients.kimi import KimiClient

logger = logging.getLogger(__name__)


class SelfHealingAgent:
    """
    Self-healing agent that handles alerts and generates hotfixes.

    This agent receives alert payloads from monitoring systems (e.g., Prometheus)
    and uses AI to analyze errors and generate automated hotfixes.
    """

    def __init__(self, kimi_client=None, orchestrator=None):
        """
        Create a SelfHealingAgent instance, initializing its Kimi client and orchestrator.
        
        If `kimi_client` or `orchestrator` are not provided, new instances are created via internal initializers.
        
        Parameters:
            kimi_client (KimiClient | None): Optional KimiClient to use; when omitted, a new client is created.
            orchestrator (RainmakerOrchestrator | None): Optional orchestrator to use; when omitted, a new orchestrator is created.
        """
        self.kimi_client = kimi_client or self._init_kimi_client()
        self.orchestrator = orchestrator or self._init_orchestrator()
        logger.info("Self-Healing Agent initialized")

    def _init_kimi_client(self):
        """
        Create and return a new KimiClient instance.
        
        Returns:
            KimiClient: A newly constructed KimiClient.
        """
        return KimiClient()

    def _init_orchestrator(self):
        """
        Initialize a new RainmakerOrchestrator instance.

        Returns:
            RainmakerOrchestrator: A new orchestrator instance
        """
        return RainmakerOrchestrator()

    def handle_alert(self, alert_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an incoming alert payload and either generate an AI-produced hotfix blueprint, acknowledge multiple alerts, or ignore empty payloads.
        
        Parameters:
            alert_payload (dict): Alert data. Expected keys:
                - description (str, optional): Error description or log used to generate a hotfix when present and no `alerts` list is provided.
                - service (str, optional): Name of the affected service; used for context in generated hotfixes.
                - alerts (list, optional): List of alert entries; when present and non-empty, the function acknowledges multiple alerts instead of generating a hotfix.
        
        Returns:
            dict: Result object with one of the following shapes:
                - {"status": "ignored", "reason": <str>} when payload lacks both `alerts` and `description`.
                - {"status": "acknowledged", "alert_count": <int>, "message": <str>} for multiple-alert payloads.
                - {"status": "hotfix_generated", "blueprint": <str>} when a hotfix blueprint is successfully produced.
                - {"status": "hotfix_failed", "error": <str>} when blueprint generation fails.
        """
        logger.info(f"Processing alert: {alert_payload.get('status', 'unknown')}")
        
        # Check for multiple alerts in payload
        alerts = alert_payload.get('alerts', [])
        if not alerts and 'description' not in alert_payload:
            return {"status": "ignored", "reason": "No alerts or description in payload"}

        error_log = alert_payload.get('description', 'No description provided')
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