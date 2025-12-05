import os
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CohereAPI:
    def __init__(self):
        try:
            import cohere
            self.cohere = cohere
 feat/production-hardening-and-keyword-research
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

            api_key = os.getenv("COHERE_API_KEY")
            if not api_key:
                logger.warning("COHERE_API_KEY not set - using mock mode")
                self.client = None
            else:
                self.client = cohere.Client(api_key)
            self.model = "command-r"
            self.usage_log = []
        except ImportError:
            logger.warning("Cohere SDK not installed - using mock mode")
            self.client = None

    def generate_content(self, prompt: str, max_tokens: int = 500) -> Dict:
        """Generate content and track usage"""
        if not self.client:
            return {
                "text": f"[MOCK] Generated content for: {prompt[:50]}...",
                "usage": {"input_tokens": 100, "output_tokens": 200, "cost_usd": 0.0}
            }

 main
        try:
            response = self.client.chat(
                model=self.model,
                message=prompt,
                max_tokens=max_tokens,
                temperature=0.7
            )

            usage = {
                "input_tokens": response.meta.tokens.input_tokens if hasattr(response.meta, 'tokens') else 100,
                "output_tokens": response.meta.tokens.output_tokens if hasattr(response.meta, 'tokens') else 200,
                "cost_usd": 0.0003  # Approximate
            }

            self.usage_log.append(usage)
            return {
                "text": response.text,
                "usage": usage
            }
        except Exception as e:
            logger.error(f"Cohere API error: {e}")
 feat/production-hardening-and-keyword-research
            raise e

            return {
                "text": f"Error generating content: {str(e)}",
                "usage": {"error": str(e)}
            }
 main

    def generate_email_sequence(self, business_type: str, days: int = 7) -> List[Dict]:
        """Generate email sequence for MailChimp"""
        sequence = []
        for day in range(1, days + 1):
            prompt = f"Write day {day} of a {days}-day email sequence for a {business_type} in South Africa. Include subject line."
            result = self.generate_content(prompt, max_tokens=300)

            lines = result["text"].split("\n")
            subject = lines[0] if lines else f"Day {day} - Your {business_type} Update"
            body = "\n".join(lines[1:]) if len(lines) > 1 else result["text"]

            sequence.append({
                "day": day,
                "subject": subject,
                "body": body
            })
        return sequence
