import os
import orjson
import re
import httpx
 feat/implement-authority-engine
from typing import Dict, Any
from hubspot import HubSpot
from .fs_agent import FileSystemAgent
from .config import ConfigManager

import logging
from typing import Dict, Any, Optional
from rainmaker_orchestrator.fs_agent import FileSystemAgent
from rainmaker_orchestrator.config import ConfigManager
from opik import track
import openlit

# Authority Engine Judge Mapping (Requested 4-Judge Protocol)
JUDGE_MODELS = {
    "visionary": "command-r-plus",
    "operator": "codestral-2501",
    "auditor": "pixtral-12b-2409",
    "challenger": "mixtral-8x22b"
}
 main

class RainmakerOrchestrator:
    \"\"\"
    The central intelligence for the Authority Engine.
    Implements a 4-Judge protocol (Visionary, Operator, Auditor, Challenger)
    with self-healing and telemetry via Opik/OpenLIT.
    \"\"\"
    def __init__(self, workspace_path: str = "./workspace", config_file: str = ".env"):
        if os.getenv("CI") != "true":
            openlit.init(
                otlp_endpoint="https://otlp.datadoghq.com:4318", 
                application_name="rainmaker-orchestrator",
                environment="production"
            )
        self.fs = FileSystemAgent(workspace_path=workspace_path)
        self.config = ConfigManager(config_file=config_file)
        self.client = httpx.AsyncClient(timeout=120.0)
        self.logger = logging.getLogger("orchestrator")

        # Centralized HubSpot Client
        hubspot_access_token = self.config.get('HUBSPOT_ACCESS_TOKEN')
        if hubspot_access_token:
            self.hubspot_client = HubSpot(access_token=hubspot_access_token)
        else:
            self.hubspot_client = None

    async def aclose(self):
        \"\"\"Gracefully close the HTTP client.\"\"\"
        await self.client.aclose()

    @track(name="judge_call")
    async def _call_judge(self, judge_role: str, context: str) -> Dict[str, Any]:
        \"\"\"Route calls to the appropriate judge model based on role.\"\"\"
        zai_key = self.config.get('ZAI_API_KEY')
        mistral_key = self.config.get('MISTRAL_API_KEY')
        
        # Priority: Z.ai (GLM) -> Mistral (Role-specific)
        if zai_key:
            api_key = zai_key
            api_base = self.config.get('ZAI_API_BASE') or "https://api.z.ai/api/paas/v4"
            model = "glm-4.7" 
        else:
            api_key = mistral_key
            api_base = self.config.get('MISTRAL_API_BASE') or "https://api.mistral.ai/v1"
            model = JUDGE_MODELS.get(judge_role, "mistral-large-latest")

        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": f"You are the {judge_role.capitalize()} Judge. Provide output in valid JSON."}, 
                {"role": "user", "content": context}
            ],
            "response_format": {"type": "json_object"}
        }
        url = f"{api_base.rstrip('/')}/chat/completions"
        response = await self.client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()

    @track(name="authority_flow")
    async def run_authority_flow(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"
        Execute the 4-Judge Authority Flow:
        1. Auditor: Analyzes compliance.
        2. Visionary: Creates strategic plan.
        3. Operator: Generates code.
        4. Challenger: Stress-tests the plan (Optional hook).
        \"\"\"
        self.logger.info("⚖\ufe0f Initiating Authority Flow...")
        
        # 1. Audit
        audit_res = await self._call_judge("auditor", f"Analyze this request for compliance: {lead_data}")
        
        # 2. Vision
        vision_res = await self._call_judge("visionary", f"Create a strategic execution plan for: {lead_data}")
        
        # 3. Operation
        op_res = await self._call_judge("operator", f"Generate implementation based on strategy: {vision_res}")
        
        return {
            "status": "success",
            "audit": audit_res['choices'][0]['message']['content'],
            "strategy": vision_res['choices'][0]['message']['content'],
            "implementation": op_res['choices'][0]['message']['content']
        }

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"Public entry point for executing varying task types.\"\"\"
        if task.get("type") == "authority_task":
            return await self.run_authority_flow(task)
        if task.get("type") == "coding_task" and task.get("output_filename"):
            return await self._run_self_healing(task)
        return {"status": "error", "message": "Task type not supported."}

    async def _run_self_healing(self, task: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"Recursive self-healing loop for generated code.\"\"\"
        filename = task["output_filename"]
        max_retries = 3
        current_context = task["context"]
        
        for i in range(max_retries):
            model_res = await self._call_judge("operator", current_context)
            content = model_res['choices'][0]['message']['content']
            try:
                # Clean JSON markdown if present
                clean_json = re.sub(r'^```json\s*|\s*```$', '', content.strip(), flags=re.MULTILINE)
                parsed = orjson.loads(clean_json)
                
                # Write and test
                self.fs.write_file(filename, parsed["code"])
                exec_result = self.fs.execute_script(filename)
                
                if exec_result["status"] == "success":
                    return {"status": "success", "output": exec_result["stdout"]}
                
                # Feedback loop
                current_context += f"\n\nRetry {i+1} - Execution Error: {exec_result.get('stderr', '')}"
            except Exception as e:
                current_context += f"\n\nRetry {i+1} - Parse Error: {str(e)}"
                
        return {"status": "failed", "message": "Max retries exceeded for self-healing."}
