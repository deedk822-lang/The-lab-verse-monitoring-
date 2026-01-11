import logging
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
        Initialize the self-healing agent.

        Args:
            kimi_client: Optional KimiClient instance. If not provided, creates a new one.
            orchestrator: Optional RainmakerOrchestrator instance. If not provided, creates a new one.
        """
        self.kimi_client = kimi_client or self._init_kimi_client()
        self.orchestrator = orchestrator or self._init_orchestrator()

    def _init_kimi_client(self):
        """
        Initialize a new KimiClient instance.

        Returns:
            KimiClient: A new KimiClient instance
        """
        return KimiClient()

    def _init_orchestrator(self):
        """
        Initialize a new RainmakerOrchestrator instance.

        Returns:
            RainmakerOrchestrator: A new orchestrator instance
        """
        return RainmakerOrchestrator()

    def handle_alert(self, alert_payload):
        """
        Handle an incoming alert and generate a hotfix.

        Receives a Prometheus Alert Manager webhook payload, analyzes the error,
        and generates an AI-powered hotfix blueprint.

        Args:
            alert_payload: Dictionary containing alert information:
                - description: Error description or log
                - service: Name of the affected service
                - severity: Alert severity level (optional)
                - labels: Additional labels (optional)
                - annotations: Additional annotations (optional)

        Returns:
            Dictionary with status and hotfix information:
            - status: 'hotfix_generated', 'hotfix_failed'
            - blueprint: Generated hotfix code (if successful)
            - error: Error message (if failed)
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
