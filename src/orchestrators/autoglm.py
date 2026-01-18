import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from ..integrations.zhipu_glm import GLMIntegration, GLMConfig
from ..integrations.alibabacloud import AlibabaCloudIntegration
from ..core.config import settings


class AutoGLMConfig(BaseModel):
    """Configuration for AutoGLM orchestrator"""
    glm_config: GLMConfig
    alibaba_config: Dict[str, str]


class AutoGLM:
    """
    AutoGLM Orchestrator
    Autonomous orchestrator combining GLM-4.7 reasoning with Alibaba Cloud security tools
    """

    def __init__(self, config: AutoGLMConfig):
        self.glm_config = config.glm_config
        self.alibaba_config = config.alibaba_config
        self.glm = None
        self.alibaba_cloud = None
        self.logger = logging.getLogger(__name__)

    async def __aenter__(self):
        """Async context manager entry"""
        self.glm = GLMIntegration(self.glm_config)
        await self.glm.__aenter__()
        self.alibaba_cloud = AlibabaCloudIntegration(self.alibaba_config)
        await self.alibaba_cloud.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.glm:
            await self.glm.__aexit__(exc_type, exc_val, exc_tb)
        if self.alibaba_cloud:
            await self.alibaba_cloud.__aexit__(exc_type, exc_val, exc_tb)

    async def autonomous_security_analysis(self) -> Dict[str, Any]:
        """
        Perform autonomous security analysis combining GLM-4.7 and Alibaba Cloud tools

        Returns:
            Comprehensive security analysis results
        """
        self.logger.info("Starting autonomous security analysis with AutoGLM...")

        try:
            # Step 1: Get current security state from Alibaba Cloud Access Analyzer
            alibaba_findings = await self.get_alibaba_security_findings()

            # Step 2: Use GLM-4.7 to analyze and provide remediation suggestions
            remediation_plan = await self.glm.generate_text(
                f"""
                Based on these Alibaba Cloud security findings, create a detailed remediation plan:
                {json.dumps(alibaba_findings, indent=2)}

                Include:
                1. Priority order for fixes
                2. Specific commands or actions needed
                3. Expected outcomes
                4. Verification steps
                """,
                {"max_tokens": 2048}
            )

            # Step 3: Execute remediation steps (simulated)
            execution_results = await self.execute_remediation_steps(remediation_plan)

            # Step 4: Verify fixes with another scan
            post_fix_findings = await self.get_alibaba_security_findings()

            # Step 5: Generate final report
            report = await self.generate_final_report(
                alibaba_findings,
                post_fix_findings,
                execution_results
            )

            return {
                "initial_findings": alibaba_findings,
                "remediation_plan": remediation_plan,
                "execution_results": execution_results,
                "post_fix_findings": post_fix_findings,
                "report": report
            }
        except Exception as e:
            self.logger.error(f"AutoGLM autonomous analysis failed: {str(e)}")
            raise

    async def get_alibaba_security_findings(self) -> List[Dict[str, Any]]:
        """Get security findings from Alibaba Cloud Access Analyzer"""
        try:
            return await self.alibaba_cloud.get_security_findings()
        except Exception as e:
            self.logger.error(f"Error getting Alibaba security findings: {str(e)}")
            return []

    async def execute_remediation_steps(self, remediation_plan: str) -> Dict[str, Any]:
        """Execute remediation steps (simulated in this implementation)"""
        self.logger.info("Executing remediation steps...")

        # Simulate execution results
        return {
            "status": "completed",
            "steps_executed": 5,
            "steps_failed": 0,
            "time_elapsed": "2m 30s",
            "summary": "All remediation steps executed successfully"
        }

    async def generate_final_report(
        self,
        initial_findings: List[Dict[str, Any]],
        post_fix_findings: List[Dict[str, Any]],
        execution_results: Dict[str, Any]
    ) -> str:
        """Generate final security report"""
        report_prompt = f"""
        Generate a comprehensive security report comparing the state before and after remediation:

        Initial findings count: {len(initial_findings)}
        Post-fix findings count: {len(post_fix_findings)}
        Execution results: {json.dumps(execution_results, indent=2)}

        Include:
        1. Executive summary
        2. Remediation effectiveness
        3. Remaining issues
        4. Recommendations for ongoing security
        """

        return await self.glm.generate_text(report_prompt)

    async def generate_secure_content(self, content_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate content with security awareness using AutoGLM

        Args:
            content_type: Type of content to generate
            context: Context for content generation

        Returns:
            Securely generated content
        """
        # First, use GLM-4.7 to generate content
        generated_content = await self.glm.generate_structured_content(content_type, context)

        # Then, analyze the generated content for security issues
        security_analysis = await self.glm.analyze_content_security(
            json.dumps(generated_content, indent=2)
        )

        # Enhance content based on security analysis
        enhanced_prompt = f"""
        Enhance this content based on security recommendations:
        Original content: {json.dumps(generated_content, indent=2)}
        Security analysis: {json.dumps(security_analysis, indent=2)}

        Return improved content that addresses the security concerns while maintaining quality.
        """

        enhanced_content = await self.glm.generate_text(enhanced_prompt)

        try:
            return json.loads(enhanced_content)
        except json.JSONDecodeError:
            return {"content": enhanced_content, "original": generated_content}

    async def learn_from_incidents(self, incident_reports: List[Dict[str, Any]]) -> str:
        """
        Learn from incidents to improve future responses

        Args:
            incident_reports: List of incident reports

        Returns:
            Learning insights
        """
        learning_prompt = f"""
        Learn from these security incidents and improve future responses:
        {json.dumps(incident_reports, indent=2)}

        Provide insights on:
        1. Common patterns
        2. Prevention strategies
        3. Detection improvements
        4. Response optimizations
        """

        return await self.glm.generate_text(learning_prompt)


# Factory function for creating AutoGLM orchestrator
async def create_autoglm_orchestrator() -> AutoGLM:
    """Factory function to create AutoGLM orchestrator"""
    config = AutoGLMConfig(
        glm_config=GLMConfig(api_key=settings.ZHIPU_API_KEY),
        alibaba_config={
            "access_key_id": settings.ALIBABA_CLOUD_ACCESS_KEY_ID,
            "secret_key": settings.ALIBABA_CLOUD_SECRET_KEY,
            "region_id": settings.ALIBABA_CLOUD_REGION_ID
        }
    )
    return AutoGLM(config)
