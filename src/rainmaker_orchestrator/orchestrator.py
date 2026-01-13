import json
import logging
import re
 feature/elite-ci-cd-pipeline-1070897568806221897
import httpx # type: ignore
from typing import Dict, Any, List, Optional
from .config import ConfigManager
from .fs_agent import FileSystemAgent as FSAgent

logger = logging.getLogger(__name__)

class RainmakerOrchestrator:
    def __init__(self) -> None:
        self.config = ConfigManager()
        self.fs = FSAgent()
        self.client = httpx.AsyncClient(timeout=60.0)

import httpx
from typing import Dict, Any
from rainmaker_orchestrator.fs_agent import FileSystemAgent
from rainmaker_orchestrator.config import ConfigManager
from opik import track

import openlit

class RainmakerOrchestrator:
    def __init__(self, workspace_path="./workspace", config_file=".env"):
        if os.getenv("CI") != "true":
            openlit.init(
                # This sends traces directly to Datadog's OTLP intake
                otlp_endpoint="https://otlp.datadoghq.com:4318", 
                application_name="rainmaker-orchestrator",
                environment="production"
            )
        self.fs = FileSystemAgent(workspace_path=workspace_path)
        self.config = ConfigManager(config_file=config_file)
        self.client = httpx.AsyncClient(timeout=120.0)
 main

        # Load API keys once to avoid global lookup overhead
        self.kimi_key: str = self.config.get("KIMI_API_KEY")
        self.kimi_base: str = self.config.get("KIMI_API_BASE", "https://api.moonshot.ai/v1")
        self.ollama_base: str = self.config.get("OLLAMA_API_BASE", "http://localhost:11434/api")

 feature/elite-ci-cd-pipeline-1070897568806221897
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

        execution_log: List[Dict[str, Any]] = []

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

    async def aclose(self) -> None:
        """Cleanly close the HTTP client session."""
        await self.client.aclose()

    @track(name="healer_hotfix_generation_kimi")
    async def _call_kimi(self, task: Dict[str, Any], routing: Dict[str, Any]) -> Dict[str, Any]:
        api_key = self.config.get('KIMI_API_KEY')
        if not api_key:
            raise ValueError("KIMI_API_KEY is not set.")

        api_base = self.config.get('KIMI_API_BASE')

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": task.get("model", "moonshot-v1-8k"),
            "messages": [{"role": "user", "content": task["context"]}],
            "temperature": 0.3
        }

        response = await self.client.post(
            f"{api_base}/chat/completions",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()

    @track(name="healer_hotfix_generation_ollama")
    async def _call_ollama(self, task: Dict[str, Any], routing: Dict[str, Any]) -> Dict[str, Any]:
        api_base = self.config.get('OLLAMA_API_BASE')

        payload = {
            "model": task.get("model", "llama3"),
            "prompt": task["context"],
            "stream": False
        }

        response = await self.client.post(
            f"{api_base}/generate",
            json=payload
        )
        response.raise_for_status()

        # Ollama's response for a non-streaming request is a single JSON object.
        # We need to parse its 'response' field which is a stringified JSON.
        ollama_response = response.json()
        return {"message": {"content": ollama_response.get("response", "{}")}}


    def route_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        if "ollama" in task.get("model", "").lower():
            return {"model": "ollama"}
        return {"model": "kimi"}

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        routing = self.route_task(task)

        if task.get("type") == "coding_task" and task.get("output_filename"):
            print(f"🔨 Initiating Self-Healing Coding Protocol for {task['output_filename']}...")

            filename = task["output_filename"]
            max_retries = 3
            current_try = 0
            current_context = task["context"]
            execution_log = []

            while current_try < max_retries:
                print(f"   Attempt {current_try + 1}/{max_retries}...")

                if current_try > 0:
                    last_error = execution_log[-1]
                    error_snippet = last_error.get('stderr', '')[:500]
                    timeout_message = last_error.get('message', '')
                    current_context += f"\n\nCRITICAL UPDATE: The previous code FAILED.\nError: {error_snippet}\nMessage: {timeout_message}\nDirectives: Analyze the error and rewrite the code to fix it."

                json_prompt = current_context + '\n\nSYSTEM: Respond strictly in JSON: {"explanation": "...", "code": "..."}'
                task_for_model = task.copy()
                task_for_model["context"] = json_prompt

                try:
                    if "ollama" in routing["model"]:
                        model_res = await self._call_ollama(task_for_model, routing)
                        content = model_res["message"]["content"]
                    else:
                        model_res = await self._call_kimi(task_for_model, routing)
                        content = model_res["choices"][0]["message"]["content"]
                except (httpx.HTTPStatusError, ValueError) as e:
                    print(f"   API Call Error: {e}")
                    return {"status": "failed", "message": f"API call failed: {e}"}

                try:
                    json_str = re.sub(r'^```json\s*|\s*```$', '', content.strip(), flags=re.MULTILINE)
                    parsed = json.loads(json_str)
                    self.fs.write_file(filename, parsed["code"])
                except Exception as e:
                    print(f"   JSON Parse Error: {e}")
                    current_try += 1
                    execution_log.append({"status": "error", "message": f"Failed to parse model output: {e}"})
                    continue

                print(f"   Testing {filename}...")
                exec_result = self.fs.execute_script(filename)

                if exec_result["status"] == "success":
                    print(f"   ✅ SUCCESS! Code executed with exit code 0.")
                    return {"status": "success", "final_code_path": filename, "output": exec_result["stdout"], "retries": current_try, "explanation": parsed.get("explanation", "N/A")}

                print(f"   ❌ FAILURE. Error caught: {exec_result.get('stderr', '')[:100]}...")
                execution_log.append(exec_result)
                current_try += 1

            return {"status": "failed", "message": "Max retries exceeded.", "last_error": execution_log[-1] if execution_log else "Unknown"}

        return {"status": "error", "message": "Task type not supported."}
 main
