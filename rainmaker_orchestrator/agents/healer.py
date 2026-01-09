import logging
from rainmaker_orchestrator.clients.kimi import KimiClient

logger = logging.getLogger(__name__)

class SelfHealingAgent:
    def __init__(self, kimi_client=None):
        self.kimi_client = kimi_client or self._init_kimi_client()

    def _init_kimi_client(self, api_key=None):
        return KimiClient(api_key=api_key)

    def handle_alert(self, alert_payload):
        """
        Receives Prometheus Alert Manager Webhook
        """
        error_log = alert_payload.get('description', 'No description provided')
        service_name = alert_payload.get('service', 'Unknown service')

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
