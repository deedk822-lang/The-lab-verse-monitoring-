import os
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class MistralAPI:
    def __init__(self):
        self.host = os.getenv("MISTRAL_HOST", "http://localhost:11434")
        self.available = False

        try:
            import ollama
            self.ollama = ollama
            self.available = True
            logger.info("Ollama initialized successfully")
        except ImportError:
            logger.warning("Ollama not installed - mock mode enabled")
            self.ollama = None
            self.available = False

    def query_local(self, prompt: str, model: str = "mistral:latest") -> Dict:
        """Query local Mistral via Ollama with fallback to mock"""

        # Mock mode if Ollama unavailable
        if not self.available or self.ollama is None:
            logger.info("Using mock mode for Mistral query")
            return {
                "text": f"[MOCK] Local Mistral response for: {prompt[:50]}...",
                "model": model,
                "host": self.host,
                "mock": True
            }

        # Real Ollama query
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
                "host": self.host,
                "mock": False
            }
        except Exception as e:
            logger.error(f"Mistral API error: {e}")
            logger.info("Falling back to mock mode")
            return {
                "text": f"[FALLBACK] Error accessing Mistral: {str(e)[:50]}",
                "model": model,
                "host": self.host,
                "mock": True,
                "error": str(e)
            }