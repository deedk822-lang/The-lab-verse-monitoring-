import asyncio
import json
import logging
 feat/integrate-alibaba-access-analyzer-12183567303830527494
import re

 dual-agent-cicd-pipeline-1349139378403618497
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
 feat/integrate-alibaba-access-analyzer-12183567303830527494
    GLM-4.7 Integration Class with Security Hardening

    GLM-4.7 Integration Class
    Provides advanced reasoning and content generation capabilities
 dual-agent-cicd-pipeline-1349139378403618497
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

 feat/integrate-alibaba-access-analyzer-12183567303830527494
    def sanitize_input(self, user_input: str) -> str:
        """Prevent prompt injection by sanitizing user input"""
        # Remove potential injection patterns
        sanitized = re.sub(r'[{}[\]"\\]', '', user_input)[:1000]  # Length limit
        return f"<user_input>{sanitized}</user_input>"

    async def generate_text(self, prompt: str, options: Optional[Dict] = None) -> str:
        """
        Generate text using GLM-4.7 model with security measures

    async def generate_text(self, prompt: str, options: Optional[Dict] = None) -> str:
        """
        Generate text using GLM-4.7 model

        Args:
            prompt: Input prompt for text generation
            options: Additional options for generation

        Returns:
            Generated text response
 dual-agent-cicd-pipeline-1349139378403618497
        """
        if options is None:
            options = {}

 feat/integrate-alibaba-access-analyzer-12183567303830527494
        # Sanitize the prompt to prevent injection
        sanitized_prompt = self.sanitize_input(prompt)

        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "user", "content": sanitized_prompt}
            ],
            "temperature": options.get("temperature", 0.7),
            "max_tokens": min(options.get("max_tokens", 1024), 4096),  # Max token limit

        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": options.get("temperature", 0.7),
            "max_tokens": options.get("max_tokens", 1024),
 dual-agent-cicd-pipeline-1349139378403618497
            "stream": False
        }

        try:
            async with self.session.post(
                self.config.base_url,
                json=payload
            ) as response:
                if response.status != 200:
 feat/integrate-alibaba-access-analyzer-12183567303830527494
                    self.logger.error(f"GLM API returned status {response.status}: {await response.text()}")
                    raise Exception(f"GLM API returned status {response.status}")

                    raise Exception(f"GLM API returned status {response.status}: {await response.text()}")
 dual-agent-cicd-pipeline-1349139378403618497

                data = await response.json()
                return data["choices"][0]["message"]["content"]

        except Exception as e:
            self.logger.error(f"Error generating text with GLM: {str(e)}")
            raise

    async def generate_structured_content(self, content_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate structured content using GLM-4.7
 feat/integrate-alibaba-access-analyzer-12183567303830527494
        """
        # Sanitize inputs
        sanitized_context = json.dumps(context, default=str)[:2000]

        prompt = f"""
        Generate structured content of type "{content_type}" based on the following context:
        {sanitized_context}


        Args:
            content_type: Type of content to generate
            context: Context for content generation

        Returns:
            Structured content dictionary
        """
        prompt = f"""
        Generate structured content of type "{content_type}" based on the following context:
        {json.dumps(context, indent=2)}
 dual-agent-cicd-pipeline-1349139378403618497

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
 feat/integrate-alibaba-access-analyzer-12183567303830527494
        """
        # Sanitize content input
        sanitized_content = self.sanitize_input(content)

        prompt = f"""
        Analyze the following content for potential security issues:
        {sanitized_content}


        Args:
            content: Content to analyze for security issues

        Returns:
            Security analysis results
        """
        prompt = f"""
        Analyze the following content for potential security issues:
        {content}
 dual-agent-cicd-pipeline-1349139378403618497

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
