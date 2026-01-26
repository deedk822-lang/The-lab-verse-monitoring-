import os
from typing import Dict, List
import logging
from .sanitizers import sanitize_prompt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CohereAPI:
    def __init__(self):
        try:
            import cohere
        except ImportError:
            raise ImportError("Cohere SDK not installed. Please install it with 'pip install cohere'")

        api_key = os.getenv("COHERE_API_KEY")
        if not api_key:
            raise ValueError("COHERE_API_KEY environment variable not set.")

        self.client = cohere.Client(api_key)
        self.model = "command-r"
        self.usage_log = []

    def generate_content(self, prompt: str, max_tokens: int = 500) -> Dict:
        """Generate content and track usage"""
        sanitized_prompt = sanitize_prompt(prompt)
        try:
            response = self.client.chat(
                model=self.model, message=sanitized_prompt, max_tokens=max_tokens, temperature=0.7
            )

            input_tokens = 0
            output_tokens = 0
            if hasattr(response, "meta") and hasattr(response.meta, "tokens"):
                input_tokens = response.meta.tokens.input_tokens or 0
                output_tokens = response.meta.tokens.output_tokens or 0

            usage = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": 0.0,  # NOTE: Actual cost calculation would require model-specific pricing
            }

            self.usage_log.append(usage)
            return {"text": response.text, "usage": usage}
        except Exception as e:
            logger.error(f"Cohere API error: {e}")
            raise e

    def generate_email_sequence(self, business_type: str, days: int = 7) -> List[Dict]:
        """Generate email sequence for MailChimp"""
        sanitized_business_type = sanitize_prompt(business_type)
        sequence = []
        for day in range(1, days + 1):
            prompt = (
                f"Write day {day} of a {days}-day email sequence for a "
                f"{sanitized_business_type} in South Africa. Include subject line."
            )
            result = self.generate_content(prompt, max_tokens=300)

            lines = result["text"].split("\n")
            subject = lines[0] if lines else f"Day {day} - Your {business_type} Update"
            body = "\n".join(lines[1:]) if len(lines) > 1 else result["text"]

            sequence.append({"day": day, "subject": subject, "body": body})
        return sequence
