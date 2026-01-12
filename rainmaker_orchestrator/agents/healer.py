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
        Create a SelfHealingAgent with optional dependency injection for its clients.
        
        Parameters:
            kimi_client (KimiClient | None): Optional KimiClient instance to use for AI generation; when omitted, a new client is created.
            orchestrator (RainmakerOrchestrator | None): Optional RainmakerOrchestrator instance to use for orchestration; when omitted, a new orchestrator is created.
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
        Create and return a new RainmakerOrchestrator instance.
        
        Returns:
            RainmakerOrchestrator: A new orchestrator instance.
        """
        return RainmakerOrchestrator()

    def handle_alert(self, alert_payload):
        """
        Handle an incoming Prometheus Alertmanager payload and produce an AI-generated hotfix blueprint.
        
        Parameters:
            alert_payload (dict): Alert data with possible keys:
                - description: error description or log (optional)
                - service: affected service name (optional)
                - severity: alert severity level (optional)
                - labels: additional labels (optional)
                - annotations: additional annotations (optional)
        
        Returns:
            dict: Result object containing:
                - status: 'hotfix_generated' on success, 'hotfix_failed' on failure.
                - blueprint: generated hotfix code when status is 'hotfix_generated'.
                - error: error message when status is 'hotfix_failed'.
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
            logger.info("Generated hotfix for service=%s (len=%d)", service_name, len(blueprint))
            return {"status": "hotfix_generated", "blueprint": blueprint}
        except Exception as e:
            logger.exception("Exception while handling alert for service=%s", service_name)
            return {"status": "hotfix_failed", "error": f"{e!r}"}