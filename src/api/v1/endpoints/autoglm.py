import asyncio
import logging
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, List
from ...orchestrators.autoglm import create_autoglm_orchestrator, AutoGLM
from ...integrations.zhipu_glm import create_glm_integration, GLMIntegration
from ...core.security import get_current_user
from ...models.user import User
from ...core.config import settings


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
    # Check user permissions
    if not current_user.has_permission("glm"):
        raise HTTPException(
            status_code=403,
            detail="User does not have permission to use GLM-4.7"
        )

    try:
        async with create_glm_integration() as glm:
            content = await glm.generate_structured_content(
                request.content_type,
                request.context
            )

        return {
            "success": True,
            "content": content,
            "timestamp": asyncio.get_event_loop().time(),
            "tenant_id": current_user.tenant_id
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
    # Check user permissions
    if not current_user.has_permission("autoglm"):
        raise HTTPException(
            status_code=403,
            detail="User does not have permission to use AutoGLM"
        )

    try:
        async with create_autoglm_orchestrator() as autoglm:
            analysis = await autoglm.autonomous_security_analysis()

        return {
            "success": True,
            "analysis": analysis,
            "timestamp": asyncio.get_event_loop().time(),
            "tenant_id": current_user.tenant_id
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
    # Check user permissions
    if not current_user.has_permission("autoglm"):
        raise HTTPException(
            status_code=403,
            detail="User does not have permission to use AutoGLM"
        )

    try:
        async with create_autoglm_orchestrator() as autoglm:
            secure_content = await autoglm.generate_secure_content(
                request.content_type,
                request.context
            )

        return {
            "success": True,
            "content": secure_content,
            "timestamp": asyncio.get_event_loop().time(),
            "tenant_id": current_user.tenant_id
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
        "tenant_id": current_user.tenant_id,
        "services": {
            "glm": {"status": "not configured"},
            "autoglm": {"status": "not configured"}
        }
    }

    # Test GLM if configured and user has access
    if current_user.has_permission("glm") and settings.ZHIPU_API_KEY:
        try:
            async with create_glm_integration() as glm:
                test_response = await glm.generate_text("Hello, are you working?", {"max_tokens": 10})
                health_status["services"]["glm"] = {
                    "status": "operational",
                    "response": test_response[:20] + "..."
                }
        except Exception as e:
            health_status["services"]["glm"] = {"status": "error", "error": str(e)}

    # Test AutoGLM if configured and user has access
    if current_user.has_permission("autoglm") and settings.ZHIPU_API_KEY and settings.ALIBABA_CLOUD_ACCESS_KEY_ID:
        try:
            async with create_autoglm_orchestrator() as autoglm:
                # Just test initialization - don't run full analysis for health check
                health_status["services"]["autoglm"] = {"status": "operational"}
        except Exception as e:
            health_status["services"]["autoglm"] = {"status": "error", "error": str(e)}

    return health_status
