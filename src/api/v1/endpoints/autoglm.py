from pydantic import BaseModel, validator

class GLMGenerateRequest(BaseModel):
    content_type: str
    context: Dict[str, Any]
    options: Dict[str, Any] = {}

    @validator("content_type")
    def validate_content_type(cls, v):
        # Add validation logic here to ensure the content type is valid
        return v

class AutoGLMSecurityAnalysisRequest(BaseModel):
    pass  # No additional fields needed

class AutoGLMSecureContentRequest(BaseModel):
    content_type: str
    context: dict[str, Any]