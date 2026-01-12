import json
import logging
import re
import httpx
from typing import Dict, Any, List, Optional
from .config import ConfigManager
from .fs_agent import FileSystemAgent as FSAgent

logger = logging.getLogger(__name__)

class RainmakerOrchestrator:
    def __init__(self):
        self.config = ConfigManager()
        self.fs = FSAgent()
        self.client = httpx.AsyncClient(timeout=60.0)

        # Load API keys once to avoid global lookup overhead
        self.kimi_key = self.config.get("KIMI_API_KEY")
        self.kimi_base = self.config.get("KIMI_API_BASE", "https://api.moonshot.ai/v1")
        self.ollama_base = self.config.get("OLLAMA_API_BASE", "http://localhost:11434/api")

    async def health_check(self) -> Dict[str, Any]:
        """Validates critical dependencies for the orchestrator."""
        return {
            "status": "healthy" if self.kimi_key else "degraded",
            "capabilities": ["fs_agent", "kimi_llm" if self.kimi_key else "ollama_local"],
            "version": "0.1.0"
        }

    async def _call_kimi(self, prompt: str) -> str:
        """Securely calls the Moonshot AI (Kimi) API."""
        if not self.kimi_key:
            raise ValueError("KIMI_API_KEY is missing from configuration.")

        headers = {"Authorization": f"Bearer {self.kimi_key}"}
        payload = {
            "model": "moonshot-v1-8k",
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"}
        }

        try:
            response = await self.client.post(f"{self.kimi_base}/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.error("Invalid KIMI_API_KEY.")
            elif e.response.status_code == 429:
                logger.warning("Kimi API Rate Limit reached.")
            raise

    async def _call_ollama(self, prompt: str) -> str:
        """Calls local Ollama instance as a fallback/local provider."""
        payload = {"model": "llama3", "prompt": prompt, "stream": False}
        response = await self.client.post(f"{self.ollama_base}/generate", json=payload)
        response.raise_for_status()
        return response.json().get("response", "")

    async def execute_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orchestrates the lifecycle of a task:
        1. Routes to specific LLM
        2. Validates JSON output
        3. Executes sanitized file operations
        """
        task_type = payload.get("type", "general")
        context = payload.get("context", "")
        model_preference = payload.get("model", "kimi")
        filename = payload.get("output_filename", "generated_code.py")

        execution_log = []

        try:
            # Step 1: LLM Routing
            if model_preference == "kimi":
                content = await self._call_kimi(context)
            else:
                content = await self._call_ollama(context)

            # Step 2: Content Sanitization & Parsing
            # Strip markdown code blocks if present
            json_str = re.sub(r'^```json\s*|\s*```$', '', content.strip(), flags=re.MULTILINE)
            parsed = json.loads(json_str)

            if "code" not in parsed:
                raise KeyError("LLM response missing 'code' key.")

            # Step 3: Secure File Writing (using the sanitized fs_agent)
            self.fs.write_file(filename, parsed["code"])

            return {
                "status": "success",
                "file": filename,
                "log": execution_log
            }

        except (json.JSONDecodeError, KeyError) as e:
            logger.exception("Failed to parse model output")
            return {"status": "failed", "message": f"Parsing Error: {str(e)}", "raw": content[:100]}
        except Exception as e:
            logger.exception("Task execution encountered a fatal error")
            return {"status": "failed", "message": str(e)}

    async def aclose(self):
        """Cleanly close the HTTP client session."""
        await self.client.aclose()
