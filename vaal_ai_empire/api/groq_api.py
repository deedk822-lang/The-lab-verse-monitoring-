import os
import logging
from typing import Dict, Any, Optional
from vaal_ai_empire.api.sanitizers import sanitize_prompt
from vaal_ai_empire.api.secure_requests import create_ssrf_safe_session

logger = logging.getLogger(__name__)


class GroqAPI:
    """
    Minimal API wrapper for Groq Cloud.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            logger.warning("GROQ_API_KEY not set. GroqAPI will operate in limited mode.")
        self.base_url = "https://api.groq.com/openai/v1"
        self.secure_session = create_ssrf_safe_session()

    def generate(self, prompt: str, max_tokens: int = 500, model: str = "llama3-70b-8192") -> Dict[str, Any]:
        """
        Generate content using Groq.
        """
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is required for generation.")

        sanitized_prompt = sanitize_prompt(prompt)

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": sanitized_prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }

        try:
            response = self.secure_session.post(
                f"{self.base_url}/chat/completions", headers=headers, json=payload, timeout=30
            )
            response.raise_for_status()
            data = response.json()

            usage = data.get("usage", {})

            return {
                "text": data["choices"][0]["message"]["content"],
                "usage": usage,
                "cost_usd": self._calculate_cost(model, usage),
            }
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise

    def _calculate_cost(self, model: str, usage: Dict[str, int]) -> float:
        # Simplified cost calculation
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)

        # Approximate rates per million tokens
        rates = {
            "llama3-70b-8192": {"prompt": 0.59, "completion": 0.79},
            "llama3-8b-8192": {"prompt": 0.05, "completion": 0.08},
        }

        rate = rates.get(model, rates["llama3-70b-8192"])
        cost = (prompt_tokens * rate["prompt"] + completion_tokens * rate["completion"]) / 1_000_000
        return cost
