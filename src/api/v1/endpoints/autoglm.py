async def generate_with_glm(
    request: GLMGenerateRequest,
    current_user: User = Depends(get_current_user)
):
    # Ensure the current_user has the required permission
    if not current_user.has_permission("glm"):
        raise HTTPException(status_code=403, detail="User does not have permission to use GLM-4.7")

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
async def generate_with_glm(
    request: GLMGenerateRequest,
    current_user: User = Depends(get_current_user)
):
    # Ensure the current_user has the required permission
    if not current_user.has_permission("glm"):
        raise HTTPException(status_code=403, detail="User does not have permission to use GLM-4.7")

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
        logger.error(f"GLM generation failed: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
import logging
import time

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ...core.config import settings
from ...core.security import get_current_user
from ...integrations.zhipu_glm import create_glm_integration
from ...models.user import User
from ...orchestrators.autoglm import create_autoglm_orchestrator

logger = logging.getLogger(__name__)

class GLMGenerateRequest(BaseModel):
    """Request model for GLM content generation"""
    content_type: str
    context: dict[str, Any]
    options: dict[str, Any] = {}


class AutoGLMSecurityAnalysisRequest(BaseModel):
    """Request model for AutoGLMSecurityAnalysis"""
    pass  # No additional fields needed


class AutoGLMSecureContentRequest(BaseModel):
    """Request model for AutoGLM secure content generation"""
    content_type: str
    context: dict[str, Any]


@router.post("/generate", summary="Generate content with GLM-4.7")
async def generate_with_glm(
    request: GLMGenerateRequest,
    current_user: User = Depends(get_current_user)
):
    # Ensure the current_user has the required permission
    if not current_user.has_permission("glm"):
        raise HTTPException(status_code=403, detail="User does not have permission to use GLM-4.7")

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
        logger.error(f"GLM generation failed: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
async def generate_with_glm(
    request: GLMGenerateRequest,
    current_user: User = Depends(get_current_user)
):
    # Ensure the current_user has the required permission
    if not current_user.has_permission("glm"):
        raise HTTPException(status_code=403, detail="User does not have permission to use GLM-4.7")

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
        logger.error(f"GLM generation failed: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
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
if current_user.has_permission("glm") and settings.ZHIPU_API_KEY:
    try:
        async with create_glm_integration() as glm:
            test_response = await glm.generate_text("Hello, are you working?", {"max_tokens": 10})
            health_status["services"]["glm"] = {
                "status": "operational",
                "response": test_response[:20] + "..."
            }
    except Exception as e:
        health_status["services"]["glm"] = {"status": "error", "error": "Internal server error"}
        logger.error(f"GLM health check failed: {e!s}", exc_info=True)

# Test AutoGLM if configured and user has access
if current_user.has_permission("autoglm") and settings.ZHIPU_API_KEY and settings.ALIBABA_CLOUD_ACCESS_KEY_ID:
    try:
        async with create_autoglm_orchestrator():
            # Just test initialization - don't run full analysis for health check
            health_status["services"]["autoglm"] = {"status": "operational"}
    except Exception as e:
        health_status["services"]["autoglm"] = {"status": "error", "error": "Internal server error"}
        logger.error(f"AutoGLM health check failed: {e!s}", exc_info=True)

return health_status