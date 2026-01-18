import asyncio
import json
import logging
import re
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import aiohttp
from ..core.config import settings


class GLMConfig(BaseModel):
    """Configuration for GLM integration"""
    api_key: str = Field(..., description="Zhipu AI API Key")
    base_url: str = Field(default="https://open.bigmodel.cn/api/paas/v4/chat/completions", description="Base URL for GLM API")
    model: str = Field(default="glm-4-plus", description="Model to use")


class GLMIntegration:
    """
    GLM-4.7 Integration Class with Security Hardening
    Provides advanced reasoning and content generation capabilities
    """

    def __init__(self, config: GLMConfig):
        self.config = config
        self.session = None
        self.logger = logging.getLogger(__name__)

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    def sanitize_input(self, user_input: str) -> str:
        """Prevent prompt injection by sanitizing user input"""
        # Remove potential injection patterns
        sanitized = re.sub(r'[{}[\]"\\]', '', user_input)[:1000]  # Length limit
        return f"<user_input>{sanitized}</user_input>"

    async def generate_text(self, prompt: str, options: Optional[Dict] = None, sanitize: bool = True) -> str:
        """
        Generate text using GLM-4.7 model with security measures

        Args:
            prompt: Input prompt for text generation
            options: Additional options for generation
            sanitize: Whether to sanitize the input prompt

        Returns:
            Generated text response
        """
        if options is None:
            options = {}

        # Sanitize the prompt to prevent injection if requested
        final_prompt = self.sanitize_input(prompt) if sanitize else prompt

        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "user", "content": final_prompt}
            ],
            "temperature": options.get("temperature", 0.7),
            "max_tokens": min(options.get("max_tokens", 1024), 4096),
            "stream": False
        }

        try:
            async with self.session.post(
                self.config.base_url,
                json=payload
            ) as response:
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
        Generate structured content using GLM-4.7
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
        Analyze content for security issues using GLM-4.7
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
    Factory function to create GLM integration.
    Changed to synchronous to support 'async with create_glm_integration()'.
    """
    config = GLMConfig(api_key=settings.ZHIPU_API_KEY)
    return GLMIntegration(config)
