import os
import json
import re
import logging
from typing import Dict, Any, Optional

import httpx
import openlit
from opik import track

from rainmaker_orchestrator.config import ConfigManager
from rainmaker_orchestrator.fs_agent import FileSystemAgent

logger: logging.Logger = logging.getLogger("orchestrator")

JUDGE_MODELS: Dict[str, str] = {
    "visionary": "command-r-plus",
    "operator": "codestral-2501",
    "auditor": "pixtral-12b-2409",
    "challenger": "mixtral-8x22b",
}


class RainmakerOrchestrator:
    """
    Central intelligence for the Authority Engine.
    Implements a 4-Judge protocol with self-healing and telemetry.
    """

    def __init__(
        self,
        workspace_path: str = "./workspace",
        config_file: str = ".env",
    ) -> None:
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
                logger.info("OpenLIT initialized in orchestrator")
            except Exception as e:
                logger.warning("OpenLIT init warning: %s", e)

        self.fs: FileSystemAgent = FileSystemAgent(workspace_path=workspace_path)
        self.config: ConfigManager = ConfigManager(config_file=config_file)
        self.client: httpx.AsyncClient = httpx.AsyncClient(timeout=120.0)

    async def aclose(self) -> None:
        """Gracefully close HTTP client."""
        await self.client.aclose()
        logger.info("Orchestrator HTTP client closed")

    @track(name="judge_call")
    async def _call_judge(self, judge_role: str, context: str) -> Dict[str, Any]:
        """Route calls to the appropriate judge model based on role."""
        zai_key: Optional[str] = self.config.get("ZAI_API_KEY")
        mistral_key: Optional[str] = self.config.get("MISTRAL_API_KEY")

        if not zai_key and not mistral_key:
            logger.error("No API keys configured (ZAI_API_KEY or MISTRAL_API_KEY)")
            raise ValueError("Missing required API credentials")

        if zai_key:
            api_key: str = zai_key
            api_base: str = self.config.get("ZAI_API_BASE") or "https://api.z.ai/api/paas/v4"
            model: str = "glm-4.7"
        else:
            api_key = mistral_key  # type: ignore[assignment]
            api_base = self.config.get("MISTRAL_API_BASE") or "https://api.mistral.ai/v1"
            model = JUDGE_MODELS.get(judge_role, "mistral-large-latest")

        headers: Dict[str, str] = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        f"You are the {judge_role.capitalize()} Judge. "
                        "Provide output in valid JSON."
                    ),
                },
                {"role": "user", "content": context},
            ],
            "response_format": {"type": "json_object"},
        }
        url: str = f"{api_base.rstrip('/')}/chat/completions"

        try:
            response: httpx.Response = await self.client.post(
                url,
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            logger.info("Judge call successful: %s", judge_role)
            return response.json()
        except httpx.HTTPError as e:
            logger.error("Judge API error (%s): %s", judge_role, e)
            raise

    @track(name="authority_flow")
    async def run_authority_flow(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the 4-Judge Authority Flow:
        1. Auditor: Analyzes compliance.
        2. Visionary: Creates strategic plan.
        3. Operator: Generates code.
        4. Challenger: Stress-tests plan (future hook).
        """
        logger.info("⚖️ Initiating Authority Flow...")

        try:
            audit_res: Dict[str, Any] = await self._call_judge(
                "auditor",
                f"Analyze this request for compliance and risk: {json.dumps(lead_data)}",
            )
            vision_res: Dict[str, Any] = await self._call_judge(
                "visionary",
                f"Create a strategic execution plan: {json.dumps(lead_data)}",
            )
            op_res: Dict[str, Any] = await self._call_judge(
                "operator",
                f"Generate implementation based on strategy: {json.dumps(vision_res)}",
            )

            logger.info("Authority Flow completed successfully")
            return {
                "status": "success",
                "audit": audit_res["choices"][0]["message"]["content"],
                "strategy": vision_res["choices"][0]["message"]["content"],
                "implementation": op_res["choices"][0]["message"]["content"],
            }
        except Exception as e:
            logger.error("Authority Flow error: %s", e)
            return {"status": "error", "message": str(e)}

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Public entry point for executing varying task types."""
        task_type: str = task.get("type", "unknown")

        if task_type == "authority_task":
            return await self.run_authority_flow(task)
        if task_type == "coding_task" and task.get("output_filename"):
            return await self._run_self_healing(task)

        logger.warning("Unsupported task type: %s", task_type)
        return {"status": "error", "message": f"Task type '{task_type}' not supported"}

    async def _run_self_healing(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Recursive self-healing loop for generated code."""
        filename: str = task["output_filename"]
        max_retries: int = 3
        current_context: str = task["context"]

        for attempt in range(max_retries):
            try:
                model_res: Dict[str, Any] = await self._call_judge("operator", current_context)
                content: str = model_res["choices"][0]["message"]["content"]

                clean_json: str = re.sub(
                    r"^```json\s*|\s*```$",
                    "",
                    content.strip(),
                    flags=re.MULTILINE,
                )
                parsed: Dict[str, Any] = json.loads(clean_json)

                self.fs.write_file(filename, parsed["code"])
                exec_result: Dict[str, Any] = self.fs.execute_script(filename)

                if exec_result["status"] == "success":
                    logger.info("Self-healing succeeded on attempt %d", attempt + 1)
                    return {"status": "success", "output": exec_result["stdout"]}

                stderr: str = exec_result.get("stderr", "Unknown error")
                current_context += f"\n\nAttempt {attempt + 1} - Execution Error: {stderr}"
                logger.warning("Self-healing attempt %d failed: %s", attempt + 1, stderr)

            except json.JSONDecodeError as e:
                logger.error("JSON parse error on attempt %d: %s", attempt + 1, e)
                current_context += f"\n\nAttempt {attempt + 1} - JSON Parse Error: {e}"
            except Exception as e:
                logger.error("Self-healing error on attempt %d: %s", attempt + 1, e)
                current_context += f"\n\nAttempt {attempt + 1} - Error: {e}"

        logger.error("Max retries exceeded for self-healing")
        return {"status": "failed", "message": "Max retries exceeded for self-healing"}
