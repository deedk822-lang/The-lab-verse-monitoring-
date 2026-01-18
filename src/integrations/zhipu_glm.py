import asyncio
import json
import logging
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
    GLM-4.7 Integration Class
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

    async def generate_text(self, prompt: str, options: Optional[Dict] = None) -> str:
        """
        Generate text using GLM-4.7 model

        Args:
            prompt: Input prompt for text generation
            options: Additional options for generation

        Returns:
            Generated text response
        """
        if options is None:
            options = {}

        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": options.get("temperature", 0.7),
            "max_tokens": options.get("max_tokens", 1024),
            "stream": False
        }

        try:
            async with self.session.post(
                self.config.base_url,
                json=payload
            ) as response:
                if response.status != 200:
                    raise Exception(f"GLM API returned status {response.status}: {await response.text()}")

                data = await response.json()
                return data["choices"][0]["message"]["content"]

        except Exception as e:
            self.logger.error(f"Error generating text with GLM: {str(e)}")
            raise

    async def generate_structured_content(self, content_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate structured content using GLM-4.7

        Args:
            content_type: Type of content to generate
            context: Context for content generation

        Returns:
            Structured content dictionary
        """
        prompt = f"""
        Generate structured content of type "{content_type}" based on the following context:
        {json.dumps(context, indent=2)}

        Respond in valid JSON format with the following structure:
        {{
            "title": "...",
            "content": "...",
            "tags": [...],
            "metadata": {{...}}
        }}
        """

        response = await self.generate_text(prompt, {"max_tokens": 2048})

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            self.logger.warning("Failed to parse GLM response as JSON, returning raw text")
            return {"content": response}

    async def analyze_content_security(self, content: str) -> Dict[str, Any]:
        """
        Analyze content for security issues using GLM-4.7

        Args:
            content: Content to analyze for security issues

        Returns:
            Security analysis results
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

        response = await self.generate_text(prompt, {"max_tokens": 2048})

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            self.logger.warning("Failed to parse security analysis as JSON")
            return {"analysis": response}


# For backward compatibility
async def create_glm_integration() -> GLMIntegration:
    """Factory function to create GLM integration"""
    config = GLMConfig(api_key=settings.ZHIPU_API_KEY)
    return GLMIntegration(config)
