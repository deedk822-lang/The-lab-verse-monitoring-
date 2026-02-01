from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ...core.config import settings
from ...core.security import get_current_user
from ...integrations.zhipu_glm import create_glm_integration
from ...models.user import User
from ...orchestrators.autoglm import create_autoglm_orchestrator

router = APIRouter(prefix="/autoglm", tags=["autoglm"])
logger = logging.getLogger(__name__)

class GLMGenerateRequest(BaseModel):
    content_type: str
    context: Dict[str, Any]
    options: Dict[str, Any] = {}


async def validate_request(request: GLMGenerateRequest):
    if not request.content_type or not isinstance(request.context, dict):
        raise HTTPException(status_code=400, detail="Invalid request body")

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
        HTTPException: 403 if the user lacks the "glm" permission; 400 on invalid request body; 500 on internal errors during generation.
    """
    try:
        await validate_request(request)
        
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
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"GLM generation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")