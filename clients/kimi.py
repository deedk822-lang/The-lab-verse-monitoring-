import os
import asyncio
from openai import AsyncOpenAI, APIStatusError, APITimeoutError
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KimiApiClient:
    def __init__(self, api_key: str = None, base_url: str = "https://api.moonshot.cn/v1"):
        """
        Initialize the KimiApiClient by resolving an API key and configuring the AsyncOpenAI client.
        
        If `api_key` is omitted, the constructor reads the `KIMI_API_KEY` environment variable and raises a ValueError if no key is available.
        
        Parameters:
            api_key (str, optional): API key to authenticate with the Kimi API. If omitted, `KIMI_API_KEY` from the environment is used.
            base_url (str): Base URL for the Kimi API.
        
        Raises:
            ValueError: If no API key is provided and `KIMI_API_KEY` is not set in the environment.
        """
        self.api_key = api_key or os.getenv("KIMI_API_KEY")
        if not self.api_key:
            raise ValueError("KIMI_API_KEY not found in environment variables.")

        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=base_url,
        )

    async def generate_hotfix(self, prompt: str, model: str = "moonshot-v1-8k", max_retries: int = 3, initial_delay: int = 1):
        """
        Generate a production-ready hotfix text from the given prompt using the Kimi API.
        
        Attempts the chat completion call up to `max_retries` times with exponential backoff starting at `initial_delay`. Retries on request timeouts and on HTTP 429 (rate limit). Non-429 API status errors are re-raised immediately; if all retries are exhausted, a generic exception is raised.
        
        Parameters:
        	prompt (str): The user prompt describing the issue or requested hotfix.
        	model (str): Model identifier to use for the completion (default: "moonshot-v1-8k").
        	max_retries (int): Maximum number of attempts before giving up (default: 3).
        	initial_delay (int): Initial backoff delay in seconds between retries (default: 1).
        
        Returns:
        	str: The hotfix text returned in the first choice's message content.
        
        Raises:
        	APIStatusError: Re-raised for non-429 HTTP status errors from the API.
        	Exception: If all retry attempts fail or an unexpected error occurs.
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