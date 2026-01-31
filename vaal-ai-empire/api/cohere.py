import logging
import os
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CohereAPI:
    """
    Cohere API client using v2 API.

    Migrated from v1 to v2:
    - Uses cohere.ClientV2 instead of cohere.Client
    - Passes messages array instead of single string
    - Handles v2 response format
    """
    def __init__(self):
        try:
            import cohere
        except ImportError:
            raise ImportError("Cohere SDK not installed. Please install it with 'pip install cohere'")

        api_key = os.getenv("COHERE_API_KEY")
        if not api_key:
            raise ValueError("COHERE_API_KEY environment variable not set.")

        # ✅ FIX: Use SSRF-safe session
        try:
            from pr_fix_agent.security.secure_requests import create_ssrf_safe_session
            self.httpx_client = create_ssrf_safe_session()
        except ImportError:
            self.httpx_client = None

        # ✅ FIX: Use ClientV2 instead of Client
        self.client = cohere.ClientV2(api_key=api_key, httpx_client=self.httpx_client)
        self.model = "command-r-plus"
        self.usage_log = []

    def generate_content(self, prompt: str, max_tokens: int = 500, system_message: Optional[str] = None) -> Dict:
        """Generate content and track usage using v2 API"""
        try:
            # ✅ FIX: Build messages array for v2 API
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})

            # ✅ FIX: Call v2 chat API with messages array
            response = self.client.chat(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7
            )

            # ✅ FIX: Parse v2 response format
            content = None
            if hasattr(response, 'message') and hasattr(response.message, 'content'):
                if isinstance(response.message.content, list) and len(response.message.content) > 0:
                    content = response.message.content[0].text

            if content is None:
                content = getattr(response, 'text', "")

            # Extract token usage if available
            input_tokens = 0
            output_tokens = 0
            if hasattr(response, 'usage'):
                if hasattr(response.usage, 'tokens'):
                    input_tokens = response.usage.tokens.input_tokens or 0
                    output_tokens = response.usage.tokens.output_tokens or 0

            usage = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": 0.0
            }

            self.usage_log.append(usage)
            return {
                "text": content,
                "usage": usage
            }
        except Exception as e:
            logger.error(f"Cohere API error: {e}")
            raise e

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
