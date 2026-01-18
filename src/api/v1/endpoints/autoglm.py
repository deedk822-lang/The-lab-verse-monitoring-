import asyncio
import logging
 feat/integrate-alibaba-access-analyzer-12183567303830527494
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks

from fastapi import APIRouter, HTTPException, Depends
 dual-agent-cicd-pipeline-1349139378403618497
from pydantic import BaseModel
from typing import Dict, Any, List
from ...orchestrators.autoglm import create_autoglm_orchestrator, AutoGLM
from ...integrations.zhipu_glm import create_glm_integration, GLMIntegration
from ...core.security import get_current_user
from ...models.user import User
 feat/integrate-alibaba-access-analyzer-12183567303830527494
from ...core.config import settings

 dual-agent-cicd-pipeline-1349139378403618497


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
 feat/integrate-alibaba-access-analyzer-12183567303830527494
    # Check user permissions
    if not current_user.has_permission("glm"):
        raise HTTPException(
            status_code=403,
            detail="User does not have permission to use GLM-4.7"
        )


 dual-agent-cicd-pipeline-1349139378403618497
    try:
        async with create_glm_integration() as glm:
            content = await glm.generate_structured_content(
                request.content_type,
                request.context
            )

        return {
            "success": True,
            "content": content,
 feat/integrate-alibaba-access-analyzer-12183567303830527494
            "timestamp": asyncio.get_running_loop().time(),
            "tenant_id": current_user.tenant_id

            "timestamp": asyncio.get_event_loop().time()
 dual-agent-cicd-pipeline-1349139378403618497
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
 feat/integrate-alibaba-access-analyzer-12183567303830527494
    # Check user permissions
    if not current_user.has_permission("autoglm"):
        raise HTTPException(
            status_code=403,
            detail="User does not have permission to use AutoGLM"
        )


 dual-agent-cicd-pipeline-1349139378403618497
    try:
        async with create_autoglm_orchestrator() as autoglm:
            analysis = await autoglm.autonomous_security_analysis()

        return {
            "success": True,
            "analysis": analysis,
 feat/integrate-alibaba-access-analyzer-12183567303830527494
            "timestamp": asyncio.get_event_loop().time(),
            "tenant_id": current_user.tenant_id

            "timestamp": asyncio.get_event_loop().time()
 dual-agent-cicd-pipeline-1349139378403618497
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
 feat/integrate-alibaba-access-analyzer-12183567303830527494
    # Check user permissions
    if not current_user.has_permission("autoglm"):
        raise HTTPException(
            status_code=403,
            detail="User does not have permission to use AutoGLM"
        )


 dual-agent-cicd-pipeline-1349139378403618497
    try:
        async with create_autoglm_orchestrator() as autoglm:
            secure_content = await autoglm.generate_secure_content(
                request.content_type,
                request.context
            )

        return {
            "success": True,
            "content": secure_content,
 feat/integrate-alibaba-access-analyzer-12183567303830527494
            "timestamp": asyncio.get_event_loop().time(),
            "tenant_id": current_user.tenant_id

            "timestamp": asyncio.get_event_loop().time()
 dual-agent-cicd-pipeline-1349139378403618497
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
 feat/integrate-alibaba-access-analyzer-12183567303830527494
        "tenant_id": current_user.tenant_id,

 dual-agent-cicd-pipeline-1349139378403618497
        "services": {
            "glm": {"status": "not configured"},
            "autoglm": {"status": "not configured"}
        }
    }

 feat/integrate-alibaba-access-analyzer-12183567303830527494
    # Test GLM if configured and user has access
    if current_user.has_permission("glm") and settings.ZHIPU_API_KEY:

    # Test GLM if configured
    if hasattr(current_user, 'has_glm_access') and current_user.has_glm_access:
 dual-agent-cicd-pipeline-1349139378403618497
        try:
            async with create_glm_integration() as glm:
                test_response = await glm.generate_text("Hello, are you working?", {"max_tokens": 10})
                health_status["services"]["glm"] = {
                    "status": "operational",
                    "response": test_response[:20] + "..."
                }
        except Exception as e:
            health_status["services"]["glm"] = {"status": "error", "error": str(e)}

 feat/integrate-alibaba-access-analyzer-12183567303830527494
    # Test AutoGLM if configured and user has access
    if current_user.has_permission("autoglm") and settings.ZHIPU_API_KEY and settings.ALIBABA_CLOUD_ACCESS_KEY_ID:

    # Test AutoGLM if configured
    if hasattr(current_user, 'has_autoglm_access') and current_user.has_autoglm_access:
 dual-agent-cicd-pipeline-1349139378403618497
        try:
            async with create_autoglm_orchestrator() as autoglm:
                # Just test initialization - don't run full analysis for health check
                health_status["services"]["autoglm"] = {"status": "operational"}
        except Exception as e:
            health_status["services"]["autoglm"] = {"status": "error", "error": str(e)}

    return health_status
