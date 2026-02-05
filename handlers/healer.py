from orchestrator import RainmakerOrchestrator
from clients.kimi import KimiClient

class SelfHealingAgent:
    """
    An autonomous agent that detects issues from alerts and attempts to generate hotfixes.
    """
    def __init__(self, kimi_client=None, orchestrator=None):
        """
        Initializes the SelfHealingAgent.

        Args:
            kimi_client (KimiClient, optional): Client for Kimi AI model. Defaults to None.
            orchestrator (RainmakerOrchestrator, optional): Orchestrator for deploying fixes. Defaults to None.
        """
        self.kimi_client = kimi_client or self._init_kimi_client()
        self.orchestrator = orchestrator or self._init_orchestrator()

    def _init_kimi_client(self):
        """Initializes the Kimi client."""
        return KimiClient()

    def _init_orchestrator(self):
        """Initializes the Rainmaker orchestrator."""
        return RainmakerOrchestrator()

    def handle_alert(self, alert_payload):
        """
        Receives a Prometheus AlertManager webhook, analyzes the alert,
        and triggers the hotfix generation and deployment process.

        Args:
            alert_payload (dict): The alert payload from Prometheus.

        Returns:
            dict: A dictionary containing the status of the hotfix process.
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
