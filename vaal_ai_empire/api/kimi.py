import os
import logging
from typing import Dict
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from .sanitizers import sanitize_prompt

logger = logging.getLogger(__name__)

class KimiAPI:
    """
    API wrapper for a vLLM-served Kimi-Linear model, using an OpenAI-compatible client.
    """
    def __init__(self):
        self.client = OpenAI(
            base_url=os.getenv("KIMI_API_BASE", "http://localhost:8000/v1"),
            api_key=os.getenv("KIMI_API_KEY", "EMPTY")
        )
        self.model = os.getenv("KIMI_MODEL", "Qwen/Qwen-72B-Instruct")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def generate_content(self, prompt: str, system_prompt: str = "You are Kimi Linear, an expert AI assistant.") -> Dict:
        """
        Generates content using the Kimi model served by vLLM.
        """
        sanitized_prompt = sanitize_prompt(prompt)
        sanitized_system_prompt = sanitize_prompt(system_prompt)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": sanitized_system_prompt},
                    {"role": "user", "content": sanitized_prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )

            usage = response.usage
            return {
                "text": response.choices[0].message.content,
                "usage": {
                    "input_tokens": usage.prompt_tokens,
                    "output_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens,
                    "cost_usd": 0.0
                }
            }
        except Exception as e:
            logger.error(f"Error during Kimi API call: {e}")
            raise

# Usage
if __name__ == "__main__":
    kimi_api = KimiAPI()
    result = kimi_api.generate_content("Explain attention mechanisms in 2 sentences.")
    print(result)
