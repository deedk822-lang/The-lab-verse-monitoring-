import json
import logging
import re
from typing import Any, Dict, Optional

import aiohttp
from pydantic import BaseModel, Field

from ..core.config import settings


class GLMConfig(BaseModel):
    """Configuration for GLM integration"""

    api_key: str = Field(..., description="Zhipu AI API Key")
    base_url: str = Field(
        default="https://open.bigmodel.cn/api/paas/v4/chat/completions", description="Base URL for GLM API"
    )
    model: str = Field(default="glm-4-plus", description="Model to use")


class GLMIntegration:
    """
    GLM-4.7 Integration Class with Security Hardening
    Provides advanced reasoning and content generation capabilities
    """

    def __init__(self, config: GLMConfig):
        """
        Initialize the GLMIntegration instance with the provided configuration and default resources.

        Parameters:
            config (GLMConfig): Configuration for the integration (includes API key, optional base_url, and model selection). The instance will store this config, initialize the HTTP session to None, and create a module-scoped logger.
        """
        self.config = config
        self.session = None
        self.logger = logging.getLogger(__name__)

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {self.config.api_key}", "Content-Type": "application/json"}
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Close the HTTP client session if one exists when exiting the async context manager.

        This ensures the underlying aiohttp ClientSession is properly closed to release network
        resources.
        """
        if self.session:
            await self.session.close()

    def sanitize_input(self, user_input: str) -> str:
        """
        Sanitize a user-provided string to mitigate prompt-injection risks.

        Removes braces, square brackets, double quotes, and backslashes from the input, truncates the result to at most 1000 characters, and wraps it in <user_input>...</user_input> tags.

        Parameters:
            user_input (str): The raw user input to sanitize.

        Returns:
            str: The sanitized and tagged input string.
        """
        # Remove potential injection patterns
        sanitized = re.sub(r'[{}[\]"\\]', "", user_input)[:1000]  # Length limit
        return f"<user_input>{sanitized}</user_input>"

    async def generate_text(self, prompt: str, options: Optional[Dict] = None, sanitize: bool = True) -> str:
        """
        Generate text from the configured GLM model using the provided prompt.

        Parameters:
            prompt (str): The user prompt to send to the model.
            options (Optional[Dict]): Optional generation parameters. Supported keys:
                - "temperature" (float): Sampling temperature (default 0.7).
                - "max_tokens" (int): Requested max tokens; effective value is capped at 4096 (default 1024).
            sanitize (bool): If True, sanitize the prompt to mitigate prompt-injection risks before sending.

        Returns:
            str: The generated text content returned by the model.

        Raises:
            Exception: If the GLM API responds with a non-200 status or if an error occurs during the request.
        """
        if options is None:
            options = {}

        # Sanitize the prompt to prevent injection if requested
        final_prompt = self.sanitize_input(prompt) if sanitize else prompt

        payload = {
            "model": self.config.model,
            "messages": [{"role": "user", "content": final_prompt}],
            "temperature": options.get("temperature", 0.7),
            "max_tokens": min(options.get("max_tokens", 1024), 4096),
            "stream": False,
        }

        try:
            async with self.session.post(self.config.base_url, json=payload) as response:
                if response.status != 200:
                    self.logger.error(f"GLM API returned status {response.status}: {await response.text()}")
                    raise Exception(f"GLM API returned status {response.status}")

                data = await response.json()
                return data["choices"][0]["message"]["content"]

        except Exception as e:
            self.logger.error(f"Error generating text with GLM: {str(e)}")
            raise

    async def generate_structured_content(self, content_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a JSON-structured piece of content of the given type using the integration's model.

        Parameters:
            content_type (str): The type/category of content to generate (e.g., "article", "summary").
            context (Dict[str, Any]): Contextual data used to inform the generated content; it will be serialized to JSON and included in the prompt.

        Returns:
            Dict[str, Any]: The parsed JSON object with keys `title`, `content`, `tags`, and `metadata` when parsing succeeds; if the model response cannot be parsed as JSON, returns `{"content": <raw_response>}`.
        """
        # Context is serialized to JSON for the prompt
        context_json = json.dumps(context, indent=2)

        prompt = f"""
        Generate structured content of type "{content_type}" based on the following context:
        {context_json}

        Respond in valid JSON format with the following structure:
        {{
            "title": "...",
            "content": "...",
            "tags": [...],
            "metadata": {{...}}
        }}
        """

        # Call generate_text with sanitize=False to preserve JSON structure in prompt
        response = await self.generate_text(prompt, {"max_tokens": 2048}, sanitize=False)

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            self.logger.warning("Failed to parse GLM response as JSON, returning raw text")
            return {"content": response}

    async def analyze_content_security(self, content: str) -> Dict[str, Any]:
        """
        Assess provided text for security vulnerabilities, compliance issues, risk factors, and remediation recommendations.

        Returns:
            dict: Parsed JSON containing the keys "vulnerabilities", "compliance_issues", "risk_factors", "recommendations", and "overall_risk_score" (0–10). If the model response cannot be parsed as JSON, returns {"analysis": <raw_response>}.
        """
        prompt = f"""
        Analyze the following content for potential security issues:
        {content}

        Identify:
        1. Potential security vulnerabilities
        2. Compliance issues
        3. Risk factors
        4. Recommendations for improvement

        Return your analysis in JSON format:
        {{
            "vulnerabilities": [...],
            "compliance_issues": [...],
            "risk_factors": [...],
            "recommendations": [...],
            "overall_risk_score": 0-10
        }}
        """

        # Call generate_text with sanitize=False to preserve content structure
        response = await self.generate_text(prompt, {"max_tokens": 2048}, sanitize=False)

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            self.logger.warning("Failed to parse security analysis as JSON")
            return {"analysis": response}


# For backward compatibility
def create_glm_integration() -> GLMIntegration:
    """
    Create a GLMIntegration configured from application settings.

    Returns:
        GLMIntegration: An integration instance initialized with settings.ZHIPU_API_KEY.
    """
    config = GLMConfig(api_key=settings.ZHIPU_API_KEY)
    return GLMIntegration(config)
