import os
import json
import re
import httpx
from typing import Dict, Any
from .fs_agent import FileSystemAgent
from .config import ConfigManager

class RainmakerOrchestrator:
    def __init__(self, workspace_path="./workspace", config_file=".env"):
        self.fs = FileSystemAgent(workspace_path=workspace_path)
        self.config = ConfigManager(config_file=config_file)
        self.client = httpx.AsyncClient(timeout=120.0)

    async def aclose(self):
        """Gracefully close the HTTP client."""
        await self.client.aclose()

    async def health_check(self) -> Dict[str, Any]:
        """Checks the health of the orchestrator and its dependencies."""
        kimi_key = self.config.get('KIMI_API_KEY')
        if not kimi_key:
            return {"status": "degraded", "reason": "KIMI_API_KEY is not set."}
        return {"status": "healthy"}

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
                except httpx.HTTPStatusError as e:
                    error_message = f"API call failed with status {e.response.status_code}"
                    if e.response.status_code == 401:
                        error_message = "HTTP 401: Invalid API key provided."
                    elif e.response.status_code == 429:
                        error_message = "HTTP 429: Rate limit exceeded or insufficient balance."

                    print(f"   API Call Error: {error_message}")
                    # In a real app, we'd use structured logging: logger.exception(...)
                    return {"status": "failed", "message": error_message}
                except ValueError as e:
                    print(f"   Configuration Error: {e}")
                    return {"status": "failed", "message": str(e)}

                try:
                    json_str = re.sub(r'^```json\s*|\s*```$', '', content.strip(), flags=re.MULTILINE)
                    parsed = json.loads(json_str)

                    if "code" not in parsed:
                        raise KeyError("The 'code' key is missing from the model's JSON response.")

                    self.fs.write_file(filename, parsed["code"])
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"   JSON Parse Error: {e}")
                    current_try += 1
                    execution_log.append({"status": "error", "message": f"Failed to parse model output: {e}. Raw content: {content[:200]}"})
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
