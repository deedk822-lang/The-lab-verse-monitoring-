from pydantic import BaseModel

class User(BaseModel):
    id: str
    email: str
    # Add has_glm_access if needed for logic
    has_glm_access: bool = True
    has_autoglm_access: bool = True
