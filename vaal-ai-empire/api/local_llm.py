"""
Local LLM API - No API keys required
Uses LocalAI or Ollama running locally
"""
import os
import requests
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class LocalLLM:
    """Local LLM wrapper - works with LocalAI or Ollama"""

    def __init__(self, backend: str = "ollama", host: str = None):
        """
        Initialize local LLM client

        Args:
            backend: "ollama" or "localai"
            host: Override default host (ollama: localhost:11434, localai: localhost:8080)
        """
        self.backend = backend

        if host:
            self.host = host
        elif backend == "ollama":
            self.host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        else:  # localai
            self.host = os.getenv("LOCALAI_HOST", "http://localhost:8080")

        # Available models
        self.models = {
            "mistral": "mistral:7b-instruct",
            "llama3": "llama3:8b",
            "qwen": "qwen:7b",
            "codellama": "codellama:7b",
            "phi3": "phi3:mini",
            "gemma": "gemma:2b",
            "mixtral": "mixtral:8x7b"
        }

        self.default_model = self.models["mistral"]
        self.usage_log = []

        logger.info(f"Initialized LocalLLM with {backend} backend at {self.host}")

    def generate(self, prompt: str, max_tokens: int = 500,
                model: str = None, temperature: float = 0.7) -> Dict:
        """Generate text using local model"""
        model = model or self.default_model

        try:
            if self.backend == "ollama":
                return self._generate_ollama(prompt, model, max_tokens, temperature)
            else:
                return self._generate_localai(prompt, model, max_tokens, temperature)
        except Exception as e:
            logger.error(f"Local LLM error: {e}")
            raise e

    def _generate_ollama(self, prompt: str, model: str,
                        max_tokens: int, temperature: float) -> Dict:
        """Generate using Ollama"""
        response = requests.post(
            f"{self.host}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            },
            timeout=120
        )

        if response.status_code != 200:
            raise Exception(f"Ollama error: {response.text}")

        data = response.json()

        usage = {
            "prompt_tokens": data.get("prompt_eval_count", 0),
            "completion_tokens": data.get("eval_count", 0),
            "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
        }

        self.usage_log.append({
            "model": model,
            "usage": usage,
            "backend": "ollama"
        })

        return {
            "text": data["response"],
            "model": model,
            "usage": usage,
            "cost_usd": 0.0,  # Free!
            "backend": "ollama"
        }

    def _generate_localai(self, prompt: str, model: str,
                         max_tokens: int, temperature: float) -> Dict:
        """Generate using LocalAI"""
        response = requests.post(
            f"{self.host}/v1/completions",
            json={
                "model": model,
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature
            },
            timeout=120
        )

        if response.status_code != 200:
            raise Exception(f"LocalAI error: {response.text}")

        data = response.json()
        choice = data["choices"][0]

        usage = data.get("usage", {})

        self.usage_log.append({
            "model": model,
            "usage": usage,
            "backend": "localai"
        })

        return {
            "text": choice["text"],
            "model": model,
            "usage": usage,
            "cost_usd": 0.0,  # Free!
            "backend": "localai"
        }

    def chat(self, messages: List[Dict], model: str = None,
             max_tokens: int = 500, temperature: float = 0.7) -> Dict:
        """Multi-turn chat"""
        model = model or self.default_model

        if self.backend == "ollama":
            # Ollama chat endpoint
            response = requests.post(
                f"{self.host}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens
                    }
                },
                timeout=120
            )

            if response.status_code != 200:
                raise Exception(f"Ollama chat error: {response.text}")

            data = response.json()

            return {
                "text": data["message"]["content"],
                "message": data["message"],
                "model": model,
                "cost_usd": 0.0
            }
        else:
            # LocalAI chat endpoint
            response = requests.post(
                f"{self.host}/v1/chat/completions",
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature
                },
                timeout=120
            )

            if response.status_code != 200:
                raise Exception(f"LocalAI chat error: {response.text}")

            data = response.json()
            choice = data["choices"][0]

            return {
                "text": choice["message"]["content"],
                "message": choice["message"],
                "model": model,
                "cost_usd": 0.0
            }

    def list_models(self) -> List[str]:
        """List available local models"""
        try:
            if self.backend == "ollama":
                response = requests.get(f"{self.host}/api/tags")
                data = response.json()
                return [m["name"] for m in data.get("models", [])]
            else:
                response = requests.get(f"{self.host}/v1/models")
                data = response.json()
                return [m["id"] for m in data.get("data", [])]
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return list(self.models.values())

    def get_total_cost(self) -> float:
        """Get total cost (always 0 for local)"""
        return 0.0
