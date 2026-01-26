import re
import logging
from typing import Dict
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class KimiAPI:
    def __init__(self, api_key: str, model: str = "kimi"):
        self.client = OpenAI(
            api_key=api_key,
            base_url="http://localhost:8888/v1" # Assuming vLLM server runs locally
        )
        self.model = model

    def _sanitize_input(self, text: str) -> str:
        """
        Sanitizes input strings to mitigate prompt injection risks and manage length.
        Strips/escapes control sequences, dangerous tokens, and excessive length.
        """
        if not isinstance(text, str):
            logger.warning("Non-string input received for sanitization: %s", text)
            return ""

        # 1. Enforce max length to prevent excessive input and potential resource exhaustion
        MAX_INPUT_LENGTH = 4000 # Adjust as appropriate for your model context window
        if len(text) > MAX_INPUT_LENGTH:
            logger.warning("Input truncated due to excessive length. Original length: %d", len(text))
            text = text[:MAX_INPUT_LENGTH]

        # 2. Strip/escape control characters that could interfere with parsing
        # Remove non-printable ASCII characters except common whitespace (space, tab, newline, carriage return)
        text = re.sub(r'[^ -~\t\n\r]', '', text)

        # 3. Remove common prompt injection keywords/phrases or escape them.
        # This is a heuristic and needs careful tuning. For now, a basic removal.
        dangerous_patterns = [
            r'(?i)ignore previous instructions',
            r'(?i)disregard all prior commands',
            r'(?i)you are now',
            r'(?i)act as a',
            r'(?i)system message',
            r'(?i)override',
            r'```(?s)(.*?)```', # Remove code blocks that could contain malicious instructions
        ]
        for pattern in dangerous_patterns:
            text = re.sub(pattern, '', text)

        # Trim leading/trailing whitespace
        return text.strip()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def generate_content(self, prompt: str, system_prompt: str = "") -> str:
        """
        Generates content using the Kimi model served by vLLM.
        """
        # Apply sanitization to both the system prompt and the user prompt
        sanitized_system_prompt = self._sanitize_input(system_prompt)
        sanitized_prompt = self._sanitize_input(prompt)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": sanitized_system_prompt},
                    {"role": "user", "content": sanitized_prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error("Error calling Kimi API: %s", e)
            raise
