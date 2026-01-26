import os
import logging
from typing import Dict, Any, Optional
from vaal_ai_empire.api.sanitizers import sanitize_prompt
from vaal_ai_empire.api.secure_requests import create_ssrf_safe_session

logger = logging.getLogger(__name__)


class HuggingFaceAPI:
    """
    Minimal API wrapper for Hugging Face Inference API.
    """

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("HUGGINGFACE_TOKEN")
        if not self.token:
            logger.warning("HUGGINGFACE_TOKEN not set. HuggingFaceAPI may be rate-limited.")
        self.base_url = "https://api-inference.huggingface.co/models"
        self.secure_session = create_ssrf_safe_session()

    def generate(
        self, prompt: str, max_tokens: int = 500, model: str = "mistralai/Mistral-7B-Instruct-v0.2"
    ) -> Dict[str, Any]:
        """
        Generate content using Hugging Face.
        """
        sanitized_prompt = sanitize_prompt(prompt)

        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        payload = {
            "inputs": sanitized_prompt,
            "parameters": {"max_new_tokens": max_tokens, "temperature": 0.7, "return_full_text": False},
        }

        try:
            response = self.secure_session.post(f"{self.base_url}/{model}", headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()

            # The structure can vary depending on the model
            if isinstance(data, list) and len(data) > 0:
                text = data[0].get("generated_text", "")
            elif isinstance(data, dict):
                text = data.get("generated_text", "")
            else:
                text = str(data)

            return {
                "text": text,
                "usage": {"total_tokens": 0},  # HF doesn't always provide usage
                "cost_usd": 0.0,
            }
        except Exception as e:
            logger.error(f"Hugging Face API error: {e}")
            raise
