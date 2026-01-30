"""
Complete Observability Stack
Issues Fixed:
#11: Structured logging (Datadog-compatible)
#12: Cost tracking and budget enforcement
"""

import os
import time
import json
import threading
import structlog
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime


# ============================================================================
# FIX #11: Structured Logging (Datadog-Compatible)
# ============================================================================

def configure_structured_logging():
    """
    Configure structured logging for production

    Features:
    - JSON output (Datadog-compatible)
    - Trace IDs for correlation
    - Timestamps in ISO format
    - Log levels
    """
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(20), # logging.INFO
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

# Initialize structured logging
configure_structured_logging()
logger = structlog.get_logger()


# ============================================================================
# FIX #12: Cost Tracking and Budget Enforcement
# ============================================================================

@dataclass
class LLMCost:
    """Track LLM usage costs"""
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: float
    timestamp: str

    def to_dict(self) -> dict:
        return asdict(self)


class BudgetExceededError(Exception):
    """Raised when budget limit is exceeded"""
    pass


class CostTracker:
    """
    Track and enforce LLM usage budgets

    Features:
    - Token counting
    - Cost estimation
    - Budget limits
    - Usage reports
    """

    # Cost per 1M tokens (approximate for Ollama - adjust for your setup)
    MODEL_COSTS = {
        "deepseek-r1:14b": 0.0,  # Free (local)
        "qwen2.5-coder:32b": 0.0,  # Free (local)
        "codellama:34b": 0.0,  # Free (local)
        "gpt-4": 30.0,  # $30 per 1M tokens (if using OpenAI)
        "claude-3": 15.0,  # $15 per 1M tokens (if using Anthropic)
    }

    def __init__(self, budget_limit: float = 100.0):
        """
        Initialize cost tracker

        Args:
            budget_limit: Maximum spend in dollars
        """
        self.budget_limit = budget_limit
        self.total_cost = 0.0
        self.usage_history: List[LLMCost] = []
        self._lock = threading.Lock()

    def record_usage(
        self,
        model: str,
        prompt: str,
        response: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> LLMCost:
        """
        Record LLM usage and calculate cost

        Args:
            model: Model name
            prompt: Input prompt
            response: Model response
            metadata: Additional metadata

        Returns:
            LLMCost object with details

        Raises:
            BudgetExceededError: If budget limit exceeded
        """
        # Estimate tokens (rough approximation: 1 token ≈ 4 chars)
        prompt_tokens = len(prompt) // 4
        completion_tokens = len(response) // 4
        total_tokens = prompt_tokens + completion_tokens

        # Calculate cost
        cost_per_million = self.MODEL_COSTS.get(model, 0.0)
        estimated_cost = (total_tokens / 1_000_000) * cost_per_million

        cost = LLMCost(
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost=estimated_cost,
            timestamp=datetime.utcnow().isoformat()
        )

        with self._lock:
            self.total_cost += estimated_cost
            self.usage_history.append(cost)

            # Check budget
            if self.total_cost > self.budget_limit:
                raise BudgetExceededError(
                    f"Budget exceeded: ${self.total_cost:.2f} > ${self.budget_limit:.2f}"
                )

        # Log usage
        logger.info(
            "llm_usage_recorded",
            model=model,
            tokens=total_tokens,
            cost=estimated_cost,
            total_cost=self.total_cost,
            budget_remaining=self.budget_limit - self.total_cost
        )

        return cost

    def get_report(self) -> dict:
        """Generate usage report"""
        with self._lock:
            total_tokens = sum(c.total_tokens for c in self.usage_history)

            by_model = {}
            for cost in self.usage_history:
                if cost.model not in by_model:
                    by_model[cost.model] = {
                        "calls": 0,
                        "tokens": 0,
                        "cost": 0.0
                    }
                by_model[cost.model]["calls"] += 1
                by_model[cost.model]["tokens"] += cost.total_tokens
                by_model[cost.model]["cost"] += cost.estimated_cost

            return {
                "total_calls": len(self.usage_history),
                "total_tokens": total_tokens,
                "total_cost": self.total_cost,
                "budget_limit": self.budget_limit,
                "budget_remaining": self.budget_limit - self.total_cost,
                "usage_by_model": by_model
            }
