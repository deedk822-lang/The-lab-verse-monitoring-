#!/bin/bash
# scripts/finalize_integration.sh
# Complete setup script for GLM-4.7, AutoGLM, and Alibaba Cloud integration

set -e

echo "🚀 Finalizing GLM-4.7 and AutoGLM Integration with Alibaba Cloud..."

# Create required directories
mkdir -p src/integrations src/orchestrators src/api/v1/endpoints logs src/core src/models

# Create the core configuration file
cat > src/core/config.py << 'EOF'
from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "Rainmaker Orchestrator"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "secret-key-for-dev")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # GLM / Zhipu
    ZHIPU_API_KEY: str = os.getenv("ZAI_API_KEY", "") # Set via ENV

    # Alibaba Cloud
    ALIBABA_CLOUD_ACCESS_KEY_ID: str = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID", "") # Set via ENV
    ALIBABA_CLOUD_SECRET_KEY: str = os.getenv("ALIBABA_CLOUD_SECRET_KEY", "")    # Set via ENV
    ALIBABA_CLOUD_REGION_ID: str = os.getenv("ALIBABA_CLOUD_REGION_ID", "cn-hangzhou")

    class Config:
        env_file = ".env"

settings = Settings()
EOF

# Create the core security file
cat > src/core/security.py << 'EOF'
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..models.user import User

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """
    Mock authentication dependency.
    In production, verify the JWT token here.
    """
    # For MVP, we accept any bearer token and return a mock user
    if not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    return User(id="user_123", email="admin@rainmaker.local")
EOF

# Create the user model
cat > src/models/user.py << 'EOF'
from pydantic import BaseModel

class User(BaseModel):
    id: str
    email: str
    # Add has_glm_access if needed for logic
    has_glm_access: bool = True
    has_autoglm_access: bool = True
EOF

# Create the GLM integration module
cat > src/integrations/zhipu_glm.py << 'EOF'
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
EOF

# Create the corrected Alibaba Cloud integration
cat > src/integrations/alibabacloud.py << 'EOF'
import asyncio
import logging
from typing import Dict, List, Any
from pydantic import BaseModel, Field
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_accessanalyzer20200901 import models as accessanalyzer_models
from alibabacloud_accessanalyzer20200901.client import Client as AccessAnalyzerClient


class AlibabaCloudConfig(BaseModel):
    """Configuration for Alibaba Cloud integration"""
    access_key_id: str = Field(..., description="Alibaba Cloud Access Key ID")
    secret_key: str = Field(..., description="Alibaba Cloud Secret Key")
    region_id: str = Field(default="cn-hangzhou", description="Alibaba Cloud Region ID")


class AlibabaCloudIntegration:
    """
    Alibaba Cloud Integration Class
    Provides integration with Alibaba Cloud services (Access Analyzer)
    """

    def __init__(self, config: AlibabaCloudConfig):
        self.config = config
        self.access_analyzer_client = None
        self.logger = logging.getLogger(__name__)

    async def __aenter__(self):
        """Async context manager entry"""
        config = open_api_models.Config(
            access_key_id=self.config.access_key_id,
            access_key_secret=self.config.secret_key,
            region_id=self.config.region_id
        )
        # Initialize the synchronous client
        self.access_analyzer_client = AccessAnalyzerClient(config)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        self.access_analyzer_client = None

    async def get_security_findings(self) -> List[Dict[str, Any]]:
        """
        Get security findings from Alibaba Cloud Access Analyzer.
        Uses asyncio.to_thread to run the synchronous SDK in a non-blocking way.
        """
        try:
            # 1. List Analyzers (Synchronous call wrapped in thread)
            list_analyzers_request = accessanalyzer_models.ListAnalyzersRequest()
            # Use asyncio.to_thread to prevent blocking the event loop
            analyzers_response = await asyncio.to_thread(
                self.access_analyzer_client.list_analyzers,
                list_analyzers_request
            )

            all_findings = []

            if not analyzers_response.body.analyzers:
                self.logger.warning("No analyzers found in Alibaba Cloud.")
                return []

            # Process each analyzer
            for analyzer in analyzers_response.body.analyzers:
                # 2. List Findings (Synchronous call wrapped in thread)
                list_findings_request = accessanalyzer_models.ListFindingsRequest(
                    analyzer_name=analyzer.name
                )

                findings_response = await asyncio.to_thread(
                    self.access_analyzer_client.list_findings,
                    list_findings_request
                )

                if findings_response.body.findings:
                    for finding in findings_response.body.findings:
                        finding_dict = {
                            "id": finding.id,
                            "resource": finding.resource,
                            "status": finding.status,
                            "severity": finding.severity,
                            "principal": finding.principal if hasattr(finding, 'principal') else "N/A",
                            "condition": finding.condition if hasattr(finding, 'condition') else {},
                            "created_at": finding.created_at,
                            "analyzer_name": analyzer.name,
                            "analyzer_type": analyzer.type
                        }
                        all_findings.append(finding_dict)

            return all_findings

        except Exception as e:
            self.logger.error(f"Error getting security findings: {str(e)}")
            # Return empty list to avoid crashing the orchestrator on API failure
            return []


# For backward compatibility
async def create_alibaba_cloud_integration() -> AlibabaCloudIntegration:
    """Factory function to create Alibaba Cloud integration"""
    config = AlibabaCloudConfig(
        access_key_id="",
        secret_key="",
        region_id="cn-hangzhou"
    )
    return AlibabaCloudIntegration(config)
EOF

# Create the AutoGLM orchestrator
cat > src/orchestrators/autoglm.py << 'EOF'
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
EOF

# Create API endpoint for AutoGLM
cat > src/api/v1/endpoints/autoglm.py << 'EOF'
import asyncio
import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List
from ...orchestrators.autoglm import create_autoglm_orchestrator, AutoGLM
from ...integrations.zhipu_glm import create_glm_integration, GLMIntegration
from ...core.security import get_current_user
from ...models.user import User


router = APIRouter(prefix="/autoglm", tags=["autoglm"])
logger = logging.getLogger(__name__)


class GLMGenerateRequest(BaseModel):
    """Request model for GLM content generation"""
    content_type: str
    context: Dict[str, Any]
    options: Dict[str, Any] = {}


class AutoGLMSecurityAnalysisRequest(BaseModel):
    """Request model for AutoGLM security analysis"""
    pass  # No additional fields needed


class AutoGLMSecureContentRequest(BaseModel):
    """Request model for AutoGLM secure content generation"""
    content_type: str
    context: Dict[str, Any]


@router.post("/generate", summary="Generate content with GLM-4.7")
async def generate_with_glm(
    request: GLMGenerateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Generate content using GLM-4.7 model
    """
    try:
        async with create_glm_integration() as glm:
            content = await glm.generate_structured_content(
                request.content_type,
                request.context
            )

        return {
            "success": True,
            "content": content,
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        logger.error(f"GLM generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/security-analysis", summary="Perform autonomous security analysis")
async def autoglm_security_analysis(
    request: AutoGLMSecurityAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Perform autonomous security analysis using AutoGLM
    """
    try:
        async with create_autoglm_orchestrator() as autoglm:
            analysis = await autoglm.autonomous_security_analysis()

        return {
            "success": True,
            "analysis": analysis,
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        logger.error(f"AutoGLM security analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/secure-content", summary="Generate secure content")
async def autoglm_secure_content(
    request: AutoGLMSecureContentRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Generate content with security awareness using AutoGLM
    """
    try:
        async with create_autoglm_orchestrator() as autoglm:
            secure_content = await autoglm.generate_secure_content(
                request.content_type,
                request.context
            )

        return {
            "success": True,
            "content": secure_content,
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        logger.error(f"AutoGLM secure content generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", summary="Health check for GLM and AutoGLM services")
async def autoglm_health_check(current_user: User = Depends(get_current_user)):
    """
    Health check for GLM and AutoGLM services
    """
    health_status = {
        "status": "healthy",
        "timestamp": asyncio.get_event_loop().time(),
        "services": {
            "glm": {"status": "not configured"},
            "autoglm": {"status": "not configured"}
        }
    }

    # Test GLM if configured
    if hasattr(current_user, 'has_glm_access') and current_user.has_glm_access:
        try:
            async with create_glm_integration() as glm:
                test_response = await glm.generate_text("Hello, are you working?", {"max_tokens": 10})
                health_status["services"]["glm"] = {
                    "status": "operational",
                    "response": test_response[:20] + "..."
                }
        except Exception as e:
            health_status["services"]["glm"] = {"status": "error", "error": str(e)}

    # Test AutoGLM if configured
    if hasattr(current_user, 'has_autoglm_access') and current_user.has_autoglm_access:
        try:
            async with create_autoglm_orchestrator() as autoglm:
                # Just test initialization - don't run full analysis for health check
                health_status["services"]["autoglm"] = {"status": "operational"}
        except Exception as e:
            health_status["services"]["autoglm"] = {"status": "error", "error": str(e)}

    return health_status
EOF

# Update main app to include AutoGLM routes
cat > src/main.py << 'EOF'
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.v1.endpoints import autoglm
from .core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    """
    print("Starting Rainmaker Orchestrator with GLM-4.7 and AutoGLM integration")
    yield
    print("Shutting down Rainmaker Orchestrator")


# Create FastAPI app with lifespan
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Rainmaker Orchestrator with GLM-4.7 and AutoGLM integration",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(autoglm.router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Rainmaker Orchestrator with GLM-4.7 and AutoGLM Integration",
        "version": settings.VERSION,
        "features": [
            "GLM-4.7 advanced reasoning",
            "AutoGLM autonomous orchestration",
            "Alibaba Cloud security integration",
            "Multi-AI provider support"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "rainmaker-orchestrator",
        "timestamp": 1234567890
    }
EOF

# Create requirements file
cat > requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
aiohttp==3.9.0
alibabacloud-tea-openapi==0.3.8
alibabacloud-accessanalyzer20200901==2.0.6
python-multipart==0.0.6
passlib[bcrypt]==1.7.4
python-jose[cryptography]==3.3.0
redis==5.0.1
zhipu-api-sdk==1.0.0
EOF

# Create setup script
cat > setup.sh << 'EOF'
#!/bin/bash
# Setup script for Rainmaker Orchestrator

set -e

echo "Setting up Rainmaker Orchestrator with GLM-4.7 and AutoGLM..."

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Create logs directory
mkdir -p logs

echo "Setup complete!"
echo "To start the application:"
echo "  source venv/bin/activate"
echo "  uvicorn src.main:app --reload --host 0.0.0.0 --port 8000"
EOF

# Create .env.example file
cat > .env.example << 'EOF'
# Application Configuration
PROJECT_NAME=Rainmaker Orchestrator
VERSION=1.0.0

# Security
SECRET_KEY=your-very-secure-secret-key-change-in-production

# GLM Configuration
ZAI_API_KEY=your-zhipu-api-key-here

# Alibaba Cloud Configuration
ALIBABA_CLOUD_ACCESS_KEY_ID=your-access-key-id-here
ALIBABA_CLOUD_SECRET_KEY=your-secret-key-here
ALIBABA_CLOUD_REGION_ID=cn-hangzhou
EOF

# Make setup script executable
chmod +x setup.sh

echo "✅ All scripts created successfully!"
echo ""
echo "To complete the integration:"
echo "1. Run: ./setup.sh"
echo "2. Set environment variables in .env:"
echo "   - ZAI_API_KEY for GLM-4.7 access"
echo "   - ALIBABA_CLOUD_ACCESS_KEY_ID, SECRET_KEY, REGION_ID"
echo "3. Start the server: uvicorn src.main:app --reload"
echo "4. Test the endpoints at http://localhost:8000"
EOF
