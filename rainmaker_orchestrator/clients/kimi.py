import os
import logging
from typing import Dict
from openai import OpenAI

logger = logging.getLogger(__name__)

class KimiClient:
    """
    API wrapper for Kimi model, using an OpenAI-compatible client.
    """
    def __init__(self, api_key=None):
        self.client = OpenAI(
            base_url=os.getenv("KIMI_API_BASE", "http://localhost:8000/v1"),
            api_key=api_key or os.getenv("KIMI_API_KEY", "EMPTY")
        )
        self.model = os.getenv("KIMI_MODEL", "moonshot-v1-8k")

    def generate(self, prompt: str, mode: str = "general") -> str:
        """
        Generates content using the Kimi model.
        """
        try:
            system_prompt = "You are Kimi, an expert AI assistant."
            if mode == "hotfix":
                system_prompt = "You are a senior site reliability engineer. Generate a precise patch for the reported error."

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3 if mode == "hotfix" else 0.7,
                max_tokens=1000
            )

            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error during Kimi API call: {e}")
            return f"Error: {str(e)}"
