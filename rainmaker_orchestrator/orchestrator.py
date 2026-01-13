import os
import json
import re
import httpx
import logging
from typing import Dict, Any, Optional
from rainmaker_orchestrator.fs_agent import FileSystemAgent
from rainmaker_orchestrator.config import ConfigManager
from opik import track
import openlit

# Authority Engine Judge Mapping
JUDGE_MODELS = {
    "visionary": "command-r-plus",
    "operator": "codestral-2501",
    "auditor": "pixtral-12b-2409",
    "challenger": "mixtral-8x22b"
}

class RainmakerOrchestrator:
    def __init__(self, workspace_path="./workspace", config_file=".env"):
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

    async def aclose(self):
        await self.client.aclose()

    @track(name="judge_call")
    async def _call_judge(self, judge_role: str, context: str) -> Dict[str, Any]:
        zai_key = self.config.get('ZAI_API_KEY')
        mistral_key = self.config.get('MISTRAL_API_KEY')
        
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
                {"role": "system", "content": f"You are the {judge_role.capitalize()} Judge."}, 
                {"role": "user", "content": context}
            ],
            "response_format": {"type": "json_object"}
        }
        url = f"{api_base.rstrip('/')}/chat/completions"
        response = await self.client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()

    async def _call_ollama(self, task: Dict[str, Any], routing: Dict[str, Any]) -> Dict[str, Any]:
        api_base = self.config.get('OLLAMA_API_BASE')
        payload = {"model": task.get("model", "llama3"), "prompt": task["context"], "stream": False}
        response = await self.client.post(f"{api_base}/generate", json=payload)
        response.raise_for_status()
        ollama_response = response.json()
        return {"message": {"content": ollama_response.get("response", "{}")}}

    @track(name="authority_flow")
    async def run_authority_flow(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        self.logger.info("⚖️ Initiating Authority Flow...")
        audit_res = await self._call_judge("auditor", f"Analyze this request for compliance: {lead_data.get('message_body', '')}")
        vision_res = await self._call_judge("visionary", f"Create a strategic execution plan for: {lead_data}")
        op_res = await self._call_judge("operator", f"Generate implementation code based on this plan: {vision_res}")
        return {
            "status": "success",
            "audit": audit_res['choices'][0]['message']['content'],
            "strategy": vision_res['choices'][0]['message']['content'],
            "implementation": op_res['choices'][0]['message']['content']
        }

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        if task.get("type") == "authority_task":
            return await self.run_authority_flow(task)
        if task.get("type") == "coding_task" and task.get("output_filename"):
            # Unified Self-Healing Logic here
            return await self._run_self_healing(task)
        return {"status": "error", "message": "Task type not supported."}

    async def _run_self_healing(self, task: Dict[str, Any]) -> Dict[str, Any]:
        filename = task["output_filename"]
        max_retries = 3
        current_context = task["context"]
        for i in range(max_retries):
            model_res = await self._call_judge("operator", current_context)
            content = model_res['choices'][0]['message']['content']
            try:
                parsed = json.loads(re.sub(r'^```json\s*|\s*```$', '', content.strip(), flags=re.MULTILINE))
                self.fs.write_file(filename, parsed["code"])
                exec_result = self.fs.execute_script(filename)
                if exec_result["status"] == "success": return {"status": "success", "output": exec_result["stdout"]}
                current_context += f"\n\nError: {exec_result.get('stderr', '')}"
            except: continue
        return {"status": "failed", "message": "Max retries exceeded."}
