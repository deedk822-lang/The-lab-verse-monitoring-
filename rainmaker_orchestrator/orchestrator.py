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
        """
        Run a recursive self-healing loop to generate, write, and execute code until it succeeds or retries are exhausted.

        Expects `task` to contain:
        - "output_filename" (str): path where generated code will be written.
        - "context" (str): prompt/context provided to the operator judge for code generation.

        On each attempt the method:
        - Requests code from the "operator" judge using the current context.
        - Cleans and parses a JSON payload returned by the judge; the JSON must contain a "code" field with the source to write.
        - Writes the code to `output_filename` and executes it via the FileSystemAgent.
        - If execution returns status "success", returns a payload with that stdout.
        - If execution fails or parsing/errors occur, appends the error information to the context and retries (up to three attempts).

        Returns:
        - A dict with {"status": "success", "output": <stdout>} when execution succeeds.
        - A dict with {"status": "failed", "message": "Max retries exceeded for self-healing"} if all retries fail.
        """
        filename: str = task["output_filename"]
        max_retries: int = 3
        current_context: str = task["context"]

        for attempt in range(max_retries):
            try:
                model_res: Dict[str, Any] = await self._call_judge(
                    "operator",
                    current_context,
                )
                content: str = model_res["choices"][0]["message"]["content"]

                # Clean JSON markdown if present
                clean_json: str = re.sub(
                    r"^```json\s*|\s*```$",
                    "",
                    content.strip(),
                    flags=re.MULTILINE,
                )
                parsed: Dict[str, Any] = json.loads(clean_json)

                # Write and test
                self.fs.write_file(filename, parsed["code"])
                exec_result: Dict[str, Any] = self.fs.execute_script(filename)

                if exec_result["status"] == "success":
                    logger.info(f"Self-healing succeeded on attempt {attempt + 1}")
                    return {"status": "success", "output": exec_result["stdout"]}

                # Feedback loop
                stderr: str = exec_result.get("stderr", "Unknown error")
                current_context += f"\n\nAttempt {attempt + 1} - Execution Error: {stderr}"
                logger.warning(f"Self-healing attempt {attempt + 1} failed: {stderr}")

            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error on attempt {attempt + 1}: {str(e)}")
                current_context += f"\n\nAttempt {attempt + 1} - JSON Parse Error: {str(e)}"
            except Exception as e:
                logger.error(f"Self-healing error on attempt {attempt + 1}: {str(e)}")
                current_context += f"\n\nAttempt {attempt + 1} - Error: {str(e)}"

        logger.error("Max retries exceeded for self-healing")
        return {"status": "failed", "message": "Max retries exceeded for self-healing"}

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
