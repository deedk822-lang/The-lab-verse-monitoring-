from orchestrator import RainmakerOrchestrator

from clients.kimi import KimiClient


class SelfHealingAgent:
    def __init__(self, kimi_client=None, orchestrator=None):
        self.kimi_client = kimi_client or self._init_kimi_client()
        self.orchestrator = orchestrator or self._init_orchestrator()

    def _init_kimi_client(self, api_key=None):
        # In a real implementation, this would get the API key from a secure store
        return KimiClient(api_key=api_key)

    def _init_orchestrator(self):
        return RainmakerOrchestrator()

    def handle_alert(self, alert_payload):
        """
        Receives Prometheus Alert Manager Webhook
        """
        error_log = alert_payload.get('description')
        service_name = alert_payload.get('service')

        prompt = f"""
        CRITICAL ALERT in service: {service_name}
        Error Log: {error_log}

        Task:
        1. Analyze the error.
        2. Generate a patch file to fix this specific exception.
        3. Do not refactor unrelated code.
        """

        # Trigger Kimi with "Hotfix" priority
        blueprint = self.kimi_client.generate(prompt, mode="hotfix")

        # Deploy to a "hotfix" branch, verify, and merge
        # In a real implementation, this would be a more sophisticated process
        print(f"Deploying hotfix for blueprint: {blueprint}")
        return {"status": "hotfix_deployed", "blueprint": blueprint}
