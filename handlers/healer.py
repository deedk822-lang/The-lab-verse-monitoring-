from orchestrator import RainmakerOrchestrator
from clients.kimi import KimiClient
from typing import Optional

class SelfHealingAgent:
    def __init__(self, kimi_client: Optional[KimiClient] = None, orchestrator: Optional[RainmakerOrchestrator] = None) -> None:
        self.kimi_client = kimi_client or self._init_kimi_client()
        self.orchestrator = orchestrator or self._init_orchestrator()

    def _init_kimi_client(self, api_key: Optional[str] = None) -> KimiClient:
        # In a real implementation, this would get the API key from a secure store
        return KimiClient(api_key=api_key)

    def _init_orchestrator(self) -> RainmakerOrchestrator:
        return RainmakerOrchestrator()

    def handle_alert(self, alert_payload):
        """
        Receives Prometheus Alert Manager Webhook
        """
        if not alert_payload:
            return {"status": "error", "message": "Empty alert payload"}

        error_log = alert_payload.get('description')
        service_name = alert_payload.get('service')

        if not error_log or not service_name:
            return {"status": "error", "message": "Missing required fields: description, service"}

        prompt = f"""
        CRITICAL ALERT in service: {service_name}
        Error Log: {error_log}

        Task:
        1. Analyze the error.
        2. Generate a patch file to fix this specific exception.
        3. Do not refactor unrelated code.
        """

        # Trigger Kimi with "Hotfix" priority
        try:
            blueprint = self.kimi_client.generate(prompt, mode="hotfix")
        except Exception as e:
            return {"status": "error", "message": f"Failed to generate hotfix: {e}"}

        # Deploy to a "hotfix" branch, verify, and merge
        print(f"Deploying hotfix for blueprint: {blueprint}")
        return {"status": "hotfix_deployed", "blueprint": blueprint}
