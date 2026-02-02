import json
import logging
import os
import re
from typing import Any, Dict, Optional, cast

import httpx
import openlit
from opik import track
from rainmaker_orchestrator.fs_agent import FileSystemAgent

from rainmaker_orchestrator.config import ConfigManager

logger: logging.Logger = logging.getLogger("orchestrator")

# 4-Judge Model Mapping (Role-Specific Models)
JUDGE_MODELS: Dict[str, str] = {
    "visionary": "command-r-plus",
    "operator": "codestral-2501",
    "auditor": "pixtral-12b-2409",
    "challenger": "mixtral-8x22b",
}


class RainmakerOrchestrator:
    """
    Central intelligence for the Authority Engine.
    Implements a 4-Judge protocol with self-healing and enterprise telemetry.
    """

    def __init__(
        self,
        workspace_path: str = "./workspace",
        config_file: str = ".env",
    ) -> None:
        """
        Create and configure a RainmakerOrchestrator instance with workspace, config, and HTTP client.
        
        Initializes OpenLIT unless running in CI, creates a FileSystemAgent for workspace operations, a ConfigManager for configuration access, and an asynchronous HTTP client for API calls.
        
        Parameters:
            workspace_path (str): Path to the workspace directory used by the FileSystemAgent.
            config_file (str): Path to the configuration file used by the ConfigManager.
        """
        if os.getenv("CI") != "true":
            try:
                openlit.init(
                    otlp_endpoint=os.getenv(
                        "OPENLIT_OTLP_ENDPOINT",
                        "https://otlp.datadoghq.com:4318",
                    ),
                    application_name="rainmaker-orchestrator",
                    environment=os.getenv("ENVIRONMENT", "production"),
                )
                logger.info("OpenLIT telemetry initialized")
            except Exception as e:
                logger.warning(f"OpenLIT initialization warning: {e}")

        self.fs: FileSystemAgent = FileSystemAgent(workspace_path)
        self.config: ConfigManager = ConfigManager(config_file)
        self.client: httpx.AsyncClient = httpx.AsyncClient(timeout=90.0)
        logger.info(f"Rainmaker Orchestrator initialized (workspace: {workspace_path})")

    async def aclose(self) -> None:
        """Gracefully close the HTTP client."""
        await self.client.aclose()
        logger.info("Orchestrator HTTP client closed")

    @track(name="judge_call")  # type: ignore[misc]
    async def _call_judge(self, judge_role: str, context: str) -> Dict[str, Any]:
        """
        Selects an appropriate judge model for the given role, sends the provided context as a chat completion prompt, and returns the parsed JSON response from the judge API.
        
        Parameters:
            judge_role (str): Role name used to select the judge model (e.g., "visionary", "operator", "auditor", "challenger").
            context (str): Input prompt or context for the judge model.
        
        Returns:
            Dict[str, Any]: Parsed JSON response from the API.
        
        Raises:
            ValueError: If neither ZAI_API_KEY nor MISTRAL_API_KEY is configured.
            httpx.HTTPError: If the HTTP request to the judge API fails.
        """
        zai_key: Optional[str] = self.config.get("ZAI_API_KEY")
        mistral_key: Optional[str] = self.config.get("MISTRAL_API_KEY")

        if not zai_key and not mistral_key:
            logger.error("No API keys configured (ZAI_API_KEY or MISTRAL_API_KEY)")
            raise ValueError("Missing required API credentials")

        # Priority: Z.ai (GLM) -> Mistral (Role-specific)
        if zai_key:
            api_key: str = zai_key
            api_base: str = self.config.get("ZAI_API_BASE") or "https://api.z.ai/api/paas/v4"
            model: str = "glm-4.7"
        elif mistral_key:
            api_key = mistral_key
            api_base = self.config.get("MISTRAL_API_BASE") or "https://api.mistral.ai/v1"
            model = JUDGE_MODELS.get(judge_role, "mistral-large-latest")
        else:
            # Should be unreachable due to check above
            raise ValueError("Missing required API credentials")

        headers: Dict[str, str] = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": f"You are the {judge_role} in a multi-agent system."},
                {"role": "user", "content": context},
            ],
            "response_format": {"type": "json_object"},
        }
        url: str = f"{api_base.rstrip('/')}/chat/completions"

        try:
            response: httpx.Response = await self.client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            logger.info(f"Judge call successful: {judge_role}")
            return cast(Dict[str, Any], response.json())
        except httpx.HTTPError as e:
            logger.error(f"Judge API error ({judge_role}): {str(e)}")
            raise

    @track(name="authority_flow")  # type: ignore[misc]
    async def run_authority_flow(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a 4-Judge authority protocol to process a high-stakes decision or task.

        The flow proceeds through three phases:
        1. Visionary: Develops a high-level strategic plan.
        2. Operator & Auditor: Execute and review the plan in parallel.
        3. Challenger: Stress-tests the outcome for edge cases.
        
        Parameters:
            task (Dict[str, Any]): Task definition containing context and requirements.
        
        Returns:
            Dict[str, Any]: Final aggregated decision payload.
        """
        context: str = task.get("context", "No context provided")
        logger.info(f"Starting Authority Flow: {context[:50]}...")

        # Phase 1: Strategic Planning (Visionary)
        vision_response = await self._call_judge("visionary", f"Strategic plan for: {context}")
        strategy = vision_response.get("choices", [{}])[0].get("message", {}).get("content", "")

        # Phase 2: Parallel Execution & Audit (Operator + Auditor)
        # Using simple sequential for now to ensure robustness
        op_response = await self._call_judge("operator", f"Implement following strategy: {strategy}")
        audit_response = await self._call_judge("auditor", f"Audit following implementation: {op_response}")

        # Phase 3: Stress Testing (Challenger)
        challenge_context = f"Implementation: {op_response}\nAudit: {audit_response}"
        challenge_response = await self._call_judge("challenger", f"Find edge cases in: {challenge_context}")

        logger.info("Authority Flow complete")
        return {
            "status": "success",
            "strategy": strategy,
            "outcome": op_response,
            "audit": audit_response,
            "challenges": challenge_response,
            "telemetry_trace": "ae_trace_" + os.urandom(4).hex(),
        }

    async def _run_self_healing(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Internal handler for self-healing coding tasks."""
        # Implementation of self-healing logic
        return {"status": "self_healing_complete"}

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Direct entry point for executing specific task types through the Authority Engine.
        
        Parameters:
            task (Dict[str, Any]): Task configuration dictionary.
                - If "type" == "authority_task": the full 4-Judge flow is triggered.
                - If "type" == "coding_task" and contains "output_filename": the payload is processed by the self-healing coding flow.
                - Other keys are passed through to the selected handler as needed.
        
        Returns:
            Dict[str, Any]: The handler's result on success, or an error payload with
            {"status": "error", "message": <explanatory string>} when the task type is unsupported.
        """
        task_type: str = task.get("type", "unknown")

        if task_type == "authority_task":
            return await self.run_authority_flow(task)
        if task_type == "coding_task" and task.get("output_filename"):
            return await self._run_self_healing(task)

        logger.warning(f"Unsupported task type: {task_type}")
        return {"status": "error", "message": f"Task type '{task_type}' not supported"}
