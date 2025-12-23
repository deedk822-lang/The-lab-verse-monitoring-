import os
import logging
from typing import Dict

logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    logger.warning("⚠️  OpenAI library not found. KimiAPI via vLLM will be unavailable.")
    OPENAI_AVAILABLE = False

class KimiAPI:
    """
    API wrapper for a vLLM-served Kimi-Linear model, using an OpenAI-compatible client.
    """
    def __init__(self):
        if not OPENAI_AVAILABLE:
            raise ImportError("Please install the 'openai' library to use the KimiAPI.")

        self.endpoint_url = os.getenv("KIMI_VLLM_ENDPOINT", "http://localhost:8000/v1")
        if not self.endpoint_url:
            raise ValueError("KIMI_VLLM_ENDPOINT environment variable is not set.")

        try:
            logger.info(f"🚀 Connecting to Kimi vLLM endpoint: {self.endpoint_url}...")
            # The API key is often not required for local vLLM, but we pass a placeholder.
            self.client = OpenAI(base_url=self.endpoint_url, api_key="not-needed")
            # You might want to add a health check here to confirm the connection
            logger.info("✅ Kimi vLLM client initialized.")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Kimi vLLM client: {e}")
            raise ValueError(f"Could not initialize KimiAPI: {e}")

    def generate_content(self, prompt: str, max_tokens: int = 500) -> Dict:
        """
        Generates content using the Kimi model served by vLLM.
        """
        messages = [
            {"role": "system", "content": "You are a helpful assistant provided by Moonshot-AI."},
            {"role": "user", "content": prompt}
        ]

        try:
            response = self.client.chat.completions.create(
                model="moonshotai/Kimi-Linear-48B-A3B-Instruct",
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7,
            )

            reply_text = response.choices[0].message.content.strip()
            usage = response.usage

            return {
                "text": reply_text,
                "usage": {
                    "input_tokens": usage.prompt_tokens,
                    "output_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens,
                    "cost_usd": 0.0  # Self-hosted model, no direct API cost
                }
            }
        except Exception as e:
            logger.error(f"❌ Kimi vLLM content generation failed: {e}")
            raise
