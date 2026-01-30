import os
import json
import structlog
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@dataclass
class LLMCost:
    """Cost tracking for LLM API calls"""
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    timestamp: str


class BudgetExceededError(Exception):
    """Raised when LLM usage exceeds budget"""
    pass


class CostTracker:
    """Track and enforce LLM API costs"""

    # Cost per 1M tokens (approximate for Ollama - adjust for your setup)
    MODEL_COSTS = {
        "deepseek-r1:14b": 0.0,  # Free (local)
        "deepseek-r1:7b": 0.0,   # Free (local)
        "deepseek-r1:1.5b": 0.0, # Free (local)
        "qwen2.5-coder:32b": 0.0,  # Free (local)
        "qwen2.5-coder:14b": 0.0,  # Free (local)
        "qwen2.5-coder:7b": 0.0,   # Free (local)
        "qwen2.5-coder:1.5b": 0.0, # Free (local)
        "qwen2.5:32b": 0.0,  # Free (local)
        "codellama:34b": 0.0,  # Free (local)
        "gpt-4": 30.0,  # $30 per 1M tokens (if using OpenAI)
        "o1-preview": 15.0,  # OpenAI reasoning model
        "claude-3-5-sonnet": 3.0,  # Anthropic coding model
    }

    def __init__(self, budget_usd: float = 10.0):
        self.budget_usd = budget_usd
        self.costs: list[LLMCost] = []
        self.total_spent = 0.0

    def track(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> LLMCost:
        """Track cost of an LLM call"""
        total_tokens = prompt_tokens + completion_tokens
        cost_per_million = self.MODEL_COSTS.get(model, 0.0)
        cost_usd = (total_tokens / 1_000_000) * cost_per_million

        cost = LLMCost(
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_usd=cost_usd,
            timestamp=datetime.now(timezone.utc).isoformat()
        )

        self.costs.append(cost)
        self.total_spent += cost_usd

        logger.info(
            "llm_cost_tracked",
            model=model,
            tokens=total_tokens,
            cost_usd=cost_usd,
            total_spent=self.total_spent,
            budget_remaining=self.budget_usd - self.total_spent
        )

        if self.total_spent > self.budget_usd:
            raise BudgetExceededError(
                f"Budget exceeded: ${self.total_spent:.4f} > ${self.budget_usd:.4f}"
            )

        return cost

    def get_summary(self) -> Dict[str, Any]:
        """Get cost summary"""
        return {
            "total_spent_usd": self.total_spent,
            "budget_usd": self.budget_usd,
            "remaining_usd": self.budget_usd - self.total_spent,
            "calls": len(self.costs),
            "total_tokens": sum(c.total_tokens for c in self.costs),
            "costs": [asdict(c) for c in self.costs]
        }
