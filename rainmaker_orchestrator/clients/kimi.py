import os
import logging
from typing import Optional
from openai import OpenAI, APIError

logger = logging.getLogger(__name__)

class KimiClient:
    """
    API wrapper for Kimi model, using an OpenAI-compatible client.
    """
    def __init__(self, api_key=None):
        """
        Initialize the KimiClient with an OpenAI-compatible client and configured model.
        
        Parameters:
            api_key (Optional[str]): Optional API key to use for the client. If not provided, the `KIMI_API_KEY` environment variable is used; if that is unset, the literal string `"EMPTY"` is used.
        
        Details:
            - The OpenAI client base URL is taken from `KIMI_API_BASE`, defaulting to `http://kimi-linear:8000/v1`.
            - The model name is taken from `KIMI_MODEL`, defaulting to `moonshot-v1-8k`.
        """
        self.client = OpenAI(
            base_url=os.getenv("KIMI_API_BASE", "http://kimi-linear:8000/v1"),
            api_key=api_key or os.getenv("KIMI_API_KEY", "EMPTY")
        )
        self.model = os.getenv("KIMI_MODEL", "moonshot-v1-8k")

    def generate(self, prompt: str, mode: str = "general") -> Optional[str]:
        """
        Generate content from the configured Kimi model using a mode-specific system prompt.
        
        Parameters:
            prompt (str): User prompt sent to the model.
            mode (str): Generation mode; "general" for assistant responses or "hotfix" for SRE-style patch suggestions.
        
        Returns:
            Optional[str]: Generated content string if successful, None otherwise.
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
                max_tokens=1000,
                timeout=30.0
            )

            # Validate response structure
            if not response.choices or len(response.choices) == 0:
                logger.error("Kimi API returned empty choices")
                return None

            if not response.choices[0].message.content:
                logger.error("Kimi API returned empty content")
                return None

            return response.choices[0].message.content
        except APIError as e:
            logger.exception(f"API error during Kimi API call: {e!r}")
            return None
        except Exception as e:
            logger.exception(f"Unexpected error during Kimi API call: {e!r}")
            return None

    def health_check(self) -> bool:
        """
        Performs a health check on the Kimi API.

        Returns:
            True if the API is healthy, False otherwise
        """
        try:
            self.client.models.list()
            return True
        except Exception as e:
            logger.error(f"Kimi health check failed: {e!r}")
            return False