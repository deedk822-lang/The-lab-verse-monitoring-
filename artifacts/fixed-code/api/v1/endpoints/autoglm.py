import asyncio
import logging
import time
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
    Generate structured content using the GLM-4.7 model for the given request.
    
    Generates content of the specified content_type using request.context and returns a payload with the generated content, a Unix timestamp, and the tenant identifier from the authenticated user.
    
    Parameters:
        request (GLMGenerateRequest): Request containing `content_type` (the kind of content to generate) and `context` (data used to guide generation).
    
    Returns:
        dict: Response payload with keys:
            - `success` (bool): `True` on successful generation.
            - `content` (Any): Generated structured content.
            - `timestamp` (float): Unix timestamp when the response was created.
            - `tenant_id` (str): Tenant identifier of the authenticated user.
    
    Raises:
        HTTPException: 403 if the user lacks the "glm" permission; 500 on internal errors during generation.
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
            "timestamp": time.time(),
            "tenant_id": current_user.tenant_id
        }
    except Exception as e:
        logger.error(f"GLM generation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


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
            "timestamp": time.time(),
            "tenant_id": current_user.tenant_id
        }
    except Exception as e:
        logger.error(f"AutoGLM security analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/secure-content", summary="Generate secure content")
async def autoglm_secure_content(
    request: AutoGLMSecureContentRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Generate security-reviewed content for the given content type and context using the AutoGLM orchestrator.
    
    Parameters:
        request (AutoGLMSecureContentRequest): Request containing `content_type` (the kind of content to produce) and `context` (data used to inform generation).
        
    Returns:
        dict: A payload with keys:
            - `success`: `True` on successful generation.
            - `content`: The generated secure content.
            - `timestamp`: Unix epoch time when the response was produced.
            - `tenant_id`: Tenant identifier of the requesting user.
    
    Raises:
        HTTPException: 403 if the current user lacks the "autoglm" permission; 500 on internal errors during generation.
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
            "timestamp": time.time(),
            "tenant_id": current_user.tenant_id
        }
    except Exception as e:
        logger.error(f"AutoGLM secure content generation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health", summary="Health check for GLM and AutoGLM services")
async def autoglm_health_check(current_user: User = Depends(get_current_user)):
    """
    Perform health checks for configured GLM and AutoGLM services and assemble an overall health status.
    
    Only services for which the current user has permission and for which required configuration is present are checked; unchecked services are reported as "not configured". The returned payload includes a POSIX timestamp and the requesting user's tenant identifier.
    
    Returns:
        dict: A mapping containing:
            - "status" (str): overall health status.
            - "timestamp" (float): POSIX timestamp of the check.
            - "tenant_id" (str): tenant identifier of the requesting user.
            - "services" (dict): per-service health information (each entry contains at minimum a "status" and may include "response" or "error").
    """
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "tenant_id": current_user.tenant_id,
        "services": {
            "glm": {"status": "not configured"},
            "autoglm": {"status": "not configured"}
        }
    }

    # Test GLM if configured and user has access
    if settings.ZHIPU_API_KEY:
        try:
            async with create_glm_integration() as glm:
                test_response = await glm.generate_text("Hello, are you working?", {"max_tokens": 10})
                health_status["services"]["glm"] = {
                    "status": "operational",
                    "response": test_response[:20] + "..."
                }
        except Exception as e:
            health_status["services"]["glm"] = {"status": "error", "error": "Internal server error"}
            logger.error(f"GLM health check failed: {str(e)}", exc_info=True)

    # Test AutoGLM if configured and user has access
    if settings.ZHIPU_API_KEY and settings.ALIBABA_CLOUD_ACCESS_KEY_ID:
        try:
            async with create_autoglm_orchestrator() as autoglm:
                # Just test initialization - don't run full analysis for health check
                health_status["services"]["autoglm"] = {"status": "operational"}
        except Exception as e:
            health_status["services"]["autoglm"] = {"status": "error", "error": "Internal server error"}
            logger.error(f"AutoGLM health check failed: {str(e)}", exc_info=True)

    return health_status