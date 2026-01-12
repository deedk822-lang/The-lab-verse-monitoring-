import os
import asyncio
from openai import AsyncOpenAI, APIStatusError, APITimeoutError
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KimiApiClient:
    def __init__(self, api_key: str = None, base_url: str = "https://api.moonshot.cn/v1"):
        """
        Initialize the KimiApiClient by resolving the API key and creating an AsyncOpenAI client.
        
        Parameters:
            api_key (str, optional): API key to use; if omitted, the value of the KIMI_API_KEY environment variable is used.
            base_url (str): Base URL for the Kimi/OpenAI API.
        
        Raises:
            ValueError: If no API key is provided and KIMI_API_KEY is not present in the environment.
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
        Generate a production-ready hotfix by sending the given prompt to the Kimi API, retrying on timeouts and rate limits with exponential backoff.
        
        Parameters:
            prompt (str): The user prompt describing the issue or required hotfix.
            model (str): Model identifier to use (default "moonshot-v1-8k").
            max_retries (int): Maximum number of attempts before giving up (default 3).
            initial_delay (int): Initial backoff delay in seconds between retries (default 1).
        
        Returns:
            str: The content of the first message returned by the API (the generated hotfix).
        
        Raises:
            Exception: If all retry attempts fail.
            APIStatusError: Re-raised for non-retriable API errors (status codes other than 429).
            Exception: Unexpected exceptions from the underlying client are propagated.
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