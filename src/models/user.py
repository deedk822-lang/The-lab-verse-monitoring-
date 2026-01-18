 feat/integrate-alibaba-access-analyzer-12183567303830527494
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional

class User(BaseModel):
    """
    User Model with Explicit Authorization (Least Privilege Default).
    """

    id: str
    email: str
    tenant_id: str
    created_at: datetime = Field(default_factory=datetime.now)

    # Explicitly deny by default
    has_glm_access: bool = Field(default=False, description="User has explicit permission to use GLM-4.7")
    has_autoglm_access: bool = Field(default=False, description="User has explicit permission to use AutoGLM")
    has_billing_access: bool = Field(default=False, description="User has access to billing features")

    # Validate email format
    @validator('email')
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email format')
        return v

    def has_permission(self, feature: str) -> bool:
        """Check explicit permissions"""
        return getattr(self, f'has_{feature}_access', False)

from pydantic import BaseModel

class User(BaseModel):
    id: str
    email: str
    # Add has_glm_access if needed for logic
    has_glm_access: bool = True
    has_autoglm_access: bool = True
 dual-agent-cicd-pipeline-1349139378403618497
