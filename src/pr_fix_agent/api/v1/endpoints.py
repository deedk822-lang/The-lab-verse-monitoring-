"""
API v1 routes
"""

from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ...agents.providers import AgentFactory, LLMResponse
from ...core.config import settings
from ...observability.metrics import CostTracker
from ...security.validator import SecurityValidator

router = APIRouter()

# Global instances
cost_tracker = CostTracker()
security_validator = SecurityValidator()


class GenerateRequest(BaseModel):
    """Request model for LLM generation"""

    prompt: str = Field(..., min_length=1, max_length=settings.security.max_input_length)
    provider: str = Field(default="ollama", regex="^(ollama|openai|cohere|huggingface)$")
    model: str = Field(default=None)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1000, ge=1, le=4000)


class GenerateResponse(BaseModel):
    """Response model for LLM generation"""

    content: str
    provider: str
    model: str
    cost: Dict[str, Any]
    metadata: Dict[str, Any]


@router.post("/generate", response_model=GenerateResponse)
async def generate_text(request: GenerateRequest) -> GenerateResponse:
    """Generate text using specified LLM provider"""

    # Validate input
    security_validator.validate_input(request.prompt)

    try:
        # Create agent
        agent = AgentFactory.create_agent(request.provider, cost_tracker)

        # Generate response
        async with agent:
            llm_response = await agent.generate(
                request.prompt,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )

        return GenerateResponse(
            content=llm_response.content,
            provider=llm_response.provider,
            model=llm_response.model,
            cost=llm_response.cost.model_dump(),
            metadata=llm_response.metadata,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers")
async def list_providers() -> Dict[str, Any]:
    """List available LLM providers and their status"""

    providers = {
        "ollama": {
            "available": True,  # Could check actual connectivity
            "models": [settings.llm.ollama_model],
        },
        "openai": {
            "available": bool(settings.llm.openai_api_key),
            "models": ["gpt-4", "gpt-3.5-turbo"],
        },
        "cohere": {
            "available": bool(settings.llm.cohere_api_key),
            "models": ["command", "base"],
        },
        "huggingface": {
            "available": bool(settings.llm.huggingface_api_key),
            "models": [settings.llm.huggingface_model],
        },
    }

    return {"providers": providers}


@router.get("/cost")
async def get_cost_info() -> Dict[str, Any]:
    """Get current cost tracking information"""

    return {
        "daily_budget": settings.llm.cost_budget_daily,
        "costs_today": cost_tracker.costs_today,
        "remaining_budget": max(0, settings.llm.cost_budget_daily - cost_tracker.costs_today),
        "tracking_enabled": settings.llm.enable_cost_tracking,
    }