import os
import logging
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage

logger = logging.getLogger(__name__)

class MistralAPI:
    def __init__(self):
        self.api_key = os.getenv("MISTRAL_API_KEY")
        if not self.api_key:
            raise ValueError("MISTRAL_API_KEY environment variable not set.")
        self.client = MistralClient(api_key=self.api_key)

    def generate_content(self, prompt: str, max_tokens: int = 500) -> dict:
        try:
            # Pricing for mistral-large-latest
            # Input: $8.00 / 1M tokens
            # Output: $24.00 / 1M tokens
            PRICE_PER_INPUT_TOKEN = 8.0 / 1_000_000
            PRICE_PER_OUTPUT_TOKEN = 24.0 / 1_000_000

            messages = [ChatMessage(role="user", content=prompt)]
            chat_response = self.client.chat(
                model="mistral-large-latest",
                messages=messages,
                max_tokens=max_tokens
            )

            usage = chat_response.usage
            input_tokens = usage.prompt_tokens
            output_tokens = usage.completion_tokens
            cost_usd = (input_tokens * PRICE_PER_INPUT_TOKEN) + (output_tokens * PRICE_PER_OUTPUT_TOKEN)

            return {
                "text": chat_response.choices[0].message.content,
                "usage": {
                    "output_tokens": output_tokens,
                    "input_tokens": input_tokens,
                    "total_tokens": usage.total_tokens,
                    "cost_usd": cost_usd
                }
            }
        except Exception as e:
            logger.error(f"Mistral API error: {e}")
            raise
