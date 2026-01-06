import os
import logging
from typing import Optional, Dict, Any

from orchestrator import RainmakerOrchestrator
from clients.kimi import KimiClient

# Define custom exceptions as suggested in the code review
class KimiError(Exception):
    """Base class for Kimi client errors."""
    pass

class KimiAuthError(KimiError):
    """Raised for authentication errors."""
    pass

class KimiRateLimitError(KimiError):
    """Raised for rate limit errors."""
    pass

logger = logging.getLogger(__name__)

class SelfHealingAgent:
    def __init__(self, kimi_client: Optional[KimiClient] = None, orchestrator: Optional[RainmakerOrchestrator] = None) -> None:
        self.kimi_client = kimi_client or self._init_kimi_client()
        self.orchestrator = orchestrator or self._init_orchestrator()

    def _init_kimi_client(self, api_key: Optional[str] = None) -> KimiClient:
        api_key = api_key or os.getenv("KIMI_API_KEY")
        if not api_key:
            raise ValueError("Kimi API key not provided or found in environment variables.")
        return KimiClient(api_key=api_key)

    def _init_orchestrator(self) -> RainmakerOrchestrator:
        return RainmakerOrchestrator()

    def handle_alert(self, alert_payload: Dict[str, Any]) -> Dict[str, Any]:
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

        try:
            # Trigger Kimi with "Hotfix" priority
            blueprint = self.kimi_client.generate(prompt, mode="hotfix")

            # Deploy to a "hotfix" branch, verify, and merge
            print(f"Deploying hotfix for blueprint: {blueprint}")
            return {"status": "hotfix_deployed", "blueprint": blueprint}

        except KimiAuthError as e:
            logger.error(f"Kimi authentication failed: {e}", exc_info=True)
            return {
                "status": "error",
                "code": "AUTH_FAILED",
                "message": "Unable to authenticate with AI service"
            }

        except KimiRateLimitError as e:
            logger.warning(f"Kimi rate limit exceeded: {e}")
            return {
                "status": "error",
                "code": "RATE_LIMIT",
                "message": "Service temporarily unavailable, retry after 60s",
                "retry_after": 60
            }

        except KimiError as e:
            logger.error(f"Kimi client error: {e}", exc_info=True)
            return {
                "status": "error",
                "code": "GENERATION_FAILED",
                "message": "Failed to generate hotfix blueprint"
            }

        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Network error during hotfix generation: {e}")
            return {
                "status": "error",
                "code": "NETWORK_ERROR",
                "message": "Network connectivity issue",
                "retryable": True
            }
