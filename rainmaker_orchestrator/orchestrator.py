import os
import json
import re
import httpx
from typing import Dict, Any
from rainmaker_orchestrator.fs_agent import FileSystemAgent
from rainmaker_orchestrator.config import ConfigManager
from opik import track

import openlit

class RainmakerOrchestrator:
    def __init__(self, workspace_path="./workspace", config_file=".env"):
        """
        Initialize the orchestrator, configure tracing (unless running in CI), and prepare filesystem, configuration, and HTTP client resources.
        
        This sets up OpenTelemetry tracing via OpenLit when the CI environment variable is not "true", creates a FileSystemAgent rooted at the given workspace path, loads configuration from the specified config file via ConfigManager, and instantiates an HTTPX asynchronous client with a 120-second timeout.
        
        Parameters:
            workspace_path (str): Path to the workspace directory used by the FileSystemAgent.
            config_file (str): Filename or path to the configuration file to load with ConfigManager.
        """
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

    async def aclose(self):
        """Gracefully close the HTTP client."""
        await self.client.aclose()

    @track(name="healer_hotfix_generation_kimi")
    async def _call_kimi(self, task: Dict[str, Any], routing: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call the KIMI chat completions endpoint using the task's context and return the API response as JSON.
        
        Parameters:
            task (Dict[str, Any]): Task payload; must include "context" (the user prompt). May include "model" to override the default ("moonshot-v1-8k").
            
        Returns:
            Dict[str, Any]: Parsed JSON response from the KIMI API.
        
        Raises:
            ValueError: If the `KIMI_API_KEY` configuration value is not set.
            HTTPStatusError: If the HTTP request to the KIMI API returns a non-success status.
        """
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
        """
        Send a non-streaming generation request to an Ollama backend and return the model's response content.
        
        Uses task["model"] (default "llama3") and task["context"] as the prompt when constructing the request payload.
        
        Returns:
            dict: A dictionary with shape {"message": {"content": <str>}} where `content` is the value of Ollama's "response" field (or "{}" if that field is absent).
        
        Raises:
            HTTPStatusError: If the HTTP request returns a non-success status.
        """
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
        """
        Execute a task and, for coding tasks that specify an output filename, run a self-healing coding protocol that iteratively requests code, writes it to disk, and tests execution until success or retries are exhausted.
        
        For tasks where task["type"] == "coding_task" and task["output_filename"] is provided, the method:
        - Determines the model routing for the task.
        - Repeats up to three attempts of: requesting JSON-formatted code and explanation from the model, writing the returned `code` to the specified file, and executing the file.
        - On failures, augments subsequent prompts with a concise error summary from the previous attempt to guide revisions.
        - Returns a success result when execution succeeds, or a failure result when max retries are exceeded or an API-level error occurs.
        
        Parameters:
            task (dict): Task descriptor containing at minimum:
                - "type" (str): The task type, e.g., "coding_task".
                - "output_filename" (str, optional): Path to write the generated code file.
                - "context" (str): The prompt/context sent to the model.
                - Optional model selection may be present and is used for routing.
        
        Returns:
            dict: Result object with one of the following shapes:
                - Success: {"status": "success", "final_code_path": <str>, "output": <str>, "retries": <int>, "explanation": <str>}
                - Failure due to retries: {"status": "failed", "message": "Max retries exceeded.", "last_error": <dict_or_str>}
                - Failure due to API error: {"status": "failed", "message": <error message>}
                - Unsupported task: {"status": "error", "message": "Task type not supported."}
        """
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