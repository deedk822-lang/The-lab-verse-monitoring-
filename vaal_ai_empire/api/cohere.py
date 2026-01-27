import os
import asyncio
from typing import Dict, List
import logging
# Use httpx for async requests, which is already a project dependency
import httpx
# Import the SSRF-safe session creator
from vaal_ai_empire.api.secure_requests import create_ssrf_safe_async_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cohere API endpoint
COHERE_API_URL = "https://api.cohere.ai/v1/chat"

class CohereAPI:
    """
    Asynchronous Cohere API client using httpx.
    This client is designed for non-blocking I/O operations suitable for FastAPI.
    """
    def __init__(self):
        api_key = os.getenv("COHERE_API_KEY")
        if not api_key:
            raise ValueError("COHERE_API_KEY environment variable not set.")

        # Use the SSRF-safe async session for making requests
        self.client: httpx.AsyncClient = create_ssrf_safe_async_session()
        self.client.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        })
        self.model = "command-r"
        self.usage_log = []

    async def generate_content(self, prompt: str, max_tokens: int = 500) -> Dict:
        """
        Generate content asynchronously and track usage.
        - Replaced synchronous cohere.Client with httpx.AsyncClient for non-blocking API calls.
        - Integrated SSRF-safe session for enhanced security.
        """
        payload = {
            "model": self.model,
            "message": prompt,
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }
        try:
            response = await self.client.post(COHERE_API_URL, json=payload)
            # Raise an exception for bad status codes (4xx or 5xx)
            response.raise_for_status()

            data = response.json()

            input_tokens = 0
            output_tokens = 0
            if "meta" in data and "billed_units" in data["meta"]:
                input_tokens = data["meta"]["billed_units"].get("input_tokens", 0)
                output_tokens = data["meta"]["billed_units"].get("output_tokens", 0)

            usage = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": 0.0,  # NOTE: Actual cost calculation would require model-specific pricing
            }

            self.usage_log.append(usage)
            return {
                "text": data.get("text", ""),
                "usage": usage
            }
        except httpx.RequestError as e:
            logger.error(f"Cohere API request error: {e}")
            # Re-raise as a generic exception to not expose library-specific details
            raise Exception("Failed to connect to Cohere API") from e
        except httpx.HTTPStatusError as e:
            logger.error(f"Cohere API error: {e.response.status_code} - {e.response.text}")
            raise Exception("Received an error from Cohere API") from e

    async def generate_email_sequence(self, business_type: str, days: int = 7) -> List[Dict]:
        """
        Generate email sequence for MailChimp asynchronously.
        - Optimized to run all API calls concurrently using asyncio.gather for significant speedup.
        """
        tasks = []
        for day in range(1, days + 1):
            prompt = f"Write day {day} of a {days}-day email sequence for a {business_type} in South Africa. Include subject line."
            tasks.append(self.generate_content(prompt, max_tokens=300))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        sequence = []
        for i, result in enumerate(results):
            day = i + 1
            if isinstance(result, Exception):
                logger.error(f"Failed to generate content for day {day}: {result}")
                # Optionally, add a placeholder or skip
                continue

            lines = result["text"].split("\n")
            subject = lines[0] if lines and lines[0].strip() else f"Day {day} - Your {business_type} Update"
            body = "\n".join(lines[1:]) if len(lines) > 1 else result["text"]

            sequence.append({
                "day": day,
                "subject": subject.replace("Subject: ", "").strip(),
                "body": body.strip()
            })
        return sequence

    async def close(self):
        """Close the httpx client session."""
        await self.client.aclose()
