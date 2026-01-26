import os
from typing import Dict
import logging
from .sanitizers import sanitize_prompt

logger = logging.getLogger(__name__)


class MistralAPI:
    def __init__(self):
        self.host = os.getenv("MISTRAL_HOST", "http://localhost:11434")
        try:
            import ollama

            self.ollama = ollama
        except ImportError:
            raise ImportError("Ollama not installed. Please install it with 'pip install ollama'")

    def query_local(self, prompt: str, model: str = "mistral:latest") -> Dict:
        """Query local Mistral via Ollama"""
        sanitized_prompt = sanitize_prompt(prompt)
        try:
            response = self.ollama.chat(
                model=model,
                messages=[{"role": "user", "content": sanitized_prompt}],
                options={"num_ctx": 32768, "temperature": 0.7},
            )
            return {"text": response["message"]["content"], "model": model, "host": self.host}
        except Exception as e:
            logger.error(f"Mistral API error: {e}")
            raise e
