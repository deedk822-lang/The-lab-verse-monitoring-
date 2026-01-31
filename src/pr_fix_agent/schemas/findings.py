from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
import re

class FindingSchema(BaseModel):
    file: str = Field(..., description="Path to the file containing the issue")
    line: int = Field(0, ge=0, description="Line number of the issue")
    severity: str = Field("medium", description="Severity level (low, medium, high, critical)")
    category: Optional[str] = Field(None, description="Category of the issue (security, lint, type, etc.)")
    issue: str = Field(..., max_length=1000, description="Description of the issue")
    suggestion: Optional[str] = Field(None, max_length=1000, description="Suggested fix")

    @field_validator('file')
    @classmethod
    def validate_path(cls, v: str) -> str:
        # Prevent path traversal
        if '..' in v or v.startswith('/'):
            raise ValueError("Potential path traversal detected in filename")
        # Allowed characters
        if not re.match(r'^[a-zA-Z0-9_./-]+$', v):
            raise ValueError("Invalid characters in filename")
        return v

    @field_validator('severity')
    @classmethod
    def validate_severity(cls, v: str) -> str:
        allowed = ['low', 'medium', 'high', 'critical', 'info']
        if v.lower() not in allowed:
            raise ValueError(f"Severity must be one of {allowed}")
        return v.lower()

class AnalysisSchema(BaseModel):
    root_cause: str = Field(..., max_length=500)
    fix_approach: str = Field(..., max_length=1000)
    risk_level: str = Field("low", pattern="^(low|medium|high)$")

class ProposalSchema(BaseModel):
    finding: FindingSchema
    root_cause: str
    fix_approach: str
    risk_level: str
