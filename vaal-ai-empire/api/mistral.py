import os
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class MistralAPI:
    def __init__(self):
        self.host = os.getenv("MISTRAL_HOST", "http://localhost:11434")
        try:
            import ollama
            self.ollama = ollama
 feat/production-hardening-and-keyword-research
        except ImportError:
            raise ImportError("Ollama not installed. Please install it with 'pip install ollama'")

    def query_local(self, prompt: str, model: str = "mistral:latest") -> Dict:
        """Query local Mistral via Ollama"""

            self.available = True
        except ImportError:
            logger.warning("Ollama not installed - using mock mode")
            self.available = False

    def query_local(self, prompt: str, model: str = "mistral:latest") -> Dict:
        """Query local Mistral via Ollama"""
        if not self.available:
            return {
                "text": f"[MOCK] Local Mistral response for: {prompt[:50]}...",
                "model": model,
                "host": self.host
            }

 main
        try:
            response = self.ollama.chat(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                options={
                    "num_ctx": 32768,
                    "temperature": 0.7
                }
            )
            return {
                "text": response["message"]["content"],
                "model": model,
                "host": self.host
            }
        except Exception as e:
            logger.error(f"Mistral API error: {e}")
 feat/production-hardening-and-keyword-research
            raise e

            return {
                "text": f"[MOCK] Mistral response (error: {str(e)})",
                "model": model,
                "host": self.host
            }
 main
