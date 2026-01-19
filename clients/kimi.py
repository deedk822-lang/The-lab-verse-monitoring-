import os
import asyncio
from openai import AsyncOpenAI, APIStatusError, APITimeoutError
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KimiApiClient:
    def __init__(self, api_key: str = None, base_url: str = "https://api.moonshot.cn/v1"):
        self.api_key = api_key or os.getenv("KIMI_API_KEY")
        if not self.api_key:
            raise ValueError("KIMI_API_KEY not found in environment variables.")

        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=base_url,
        )

    async def generate_hotfix(self, prompt: str, model: str = "moonshot-v1-8k", max_retries: int = 3, initial_delay: int = 1):
        """
        Generates a hotfix using the Kimi API with retry logic.
        """
        delay = initial_delay
        for attempt in range(max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a senior software engineer specialized in creating production-ready hotfixes."},
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=2048,
                    temperature=0.1,
                )
                return response.choices[0].message.content
            except APITimeoutError as e:
                logger.warning(f"Request timed out. Attempt {attempt + 1} of {max_retries}. Retrying in {delay}s...")
            except APIStatusError as e:
                if e.status_code == 429: # Rate limit error
                    logger.warning(f"Rate limit exceeded. Attempt {attempt + 1} of {max_retries}. Retrying in {delay}s...")
                else:
                    logger.error(f"API error with status code {e.status_code}: {e.message}")
                    raise  # Re-raise for non-retriable errors
            except Exception as e:
                logger.error(f"An unexpected error occurred: {e}")
                raise

            await asyncio.sleep(delay)
            delay *= 2  # Exponential backoff

        raise Exception("Failed to generate hotfix after multiple retries.")
