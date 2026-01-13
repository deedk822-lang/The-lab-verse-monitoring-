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

# Configuration for Authority Engine Judges
# When using ZAI, we map these to GLM equivalents if preferred, 
# but ZAI often proxies specialized models.
JUDGE_MODELS = {
    \"visionary\": \"command-r-plus\",
    \"operator\": \"codestral-2501\",
    \"auditor\": \"pixtral-12b-2409\",
    \"challenger\": \"mixtral-8x22b\"
}

class RainmakerOrchestrator:
    def __init__(self, workspace_path=\"./workspace\", config_file=\".env\"):
        if os.getenv(\"CI\") != \"true\":
            openlit.init(
                otlp_endpoint=\"https://otlp.datadoghq.com:4318\", 
                application_name=\"rainmaker-orchestrator\",
                environment=\"production\"
            )
        self.fs = FileSystemAgent(workspace_path=workspace_path)
        self.config = ConfigManager(config_file=config_file)
        self.client = httpx.AsyncClient(timeout=120.0)
        self.logger = logging.getLogger(\"orchestrator\")

    async def aclose(self):
        await self.client.aclose()

    @track(name=\"judge_call\")
    async def _call_judge(self, judge_role: str, context: str) -> Dict[str, Any]:
        \"\"\"Generic caller for the specialized Judges.\"\"\"
        # Mapping logic: Prioritize ZAI if key is present
        zai_key = self.config.get('ZAI_API_KEY')
        mistral_key = self.config.get('MISTRAL_API_KEY')
        
        if zai_key:
            api_key = zai_key
            api_base = self.config.get('ZAI_API_BASE') or \"https://api.z.ai/api/paas/v4\"
            # If using ZAI, default to glm-4.7 for better compatibility unless specified
            model = \"glm-4.7\" 
        else:
            api_key = mistral_key
            api_base = self.config.get('MISTRAL_API_BASE') or \"https://api.mistral.ai/v1\"
            model = JUDGE_MODELS.get(judge_role, \"mistral-large-latest\")

        headers = {\"Authorization\": f\"Bearer {api_key}\", \"Content-Type\": \"application/json\"}
        payload = {
            \"model\": model,
            \"messages\": [
                {\"role\": \"system\", \"content\": f\"You are the {judge_role.capitalize()} Judge.\"}, 
                {\"role\": \"user\", \"content\": context}
            ],
            \"response_format\": {\"type\": \"json_object\"}
        }

        # Ensure correct endpoint construction
        url = f\"{api_base.rstrip('/')}/chat/completions\"
        
        try:
            response = await self.client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f\"Judge call failed for {judge_role} using {url}: {str(e)}\")
            raise

    @track(name=\"authority_flow\")
    async def run_authority_flow(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"The canonical Authority Engine loop: Audit -> Vision -> Operation.\"\"\"
        self.logger.info(\"⚖️ Initiating Authority Flow...\")
        
        # 1. Auditor verifies logic/compliance
        audit_res = await self._call_judge(\"auditor\", f\"Analyze this request for compliance and logical consistency: {lead_data.get('message_body', '')}\")

        # 2. Visionary creates the strategic blueprint
        vision_res = await self._call_judge(\"visionary\", f\"Create a strategic execution plan for: {lead_data}\")
        
        # 3. Operator generates the implementation
        op_res = await self._call_judge(\"operator\", f\"Generate implementation code based on this plan: {vision_res}\")

        return {
            \"status\": \"success\",
            \"audit\": audit_res['choices'][0]['message']['content'],
            \"strategy\": vision_res['choices'][0]['message']['content'],
            \"implementation\": op_res['choices'][0]['message']['content']
        }

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"Entry point for task execution.\"\"\"
        if task.get(\"type\") == \"authority_task\":
            return await self.run_authority_flow(task)
        return {\"status\": \"error\", \"message\": \"Task type not supported.\"}
