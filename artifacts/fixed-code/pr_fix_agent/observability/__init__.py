"""
Observability module for PR Fix Agent.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class LLMCost(Base):
    __tablename__ = 'llm_costs'
    id = Column(Integer, primary_key=True)
    model = Column(String(50))
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    total_tokens = Column(Integer)
    cost_usd = Column(Float)
    timestamp = Column(DateTime)

class BudgetExceededError(Exception):
    """Raised when LLM usage exceeds budget"""

class CostTracker:
    """Track and enforce LLM API costs"""

    def __init__(self, db_url: str, budget_usd: float = 10.0):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)()
        self.budget_usd = budget_usd
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

        self.session.add(cost)
        self.session.commit()

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

    def get_summary(self) -> Dict[str, Any]:
        """Get cost summary"""
        return {
            "total_spent_usd": self.total_spent,
            "budget_usd": self.budget_usd,
            "remaining_usd": self.budget_usd - self.total_spent,
            "calls": len(self.session.query(LLMCost).all()),
            "total_tokens": sum(c.total_tokens for c in self.session.query(LLMCost).all()),
            "costs": [asdict(c) for c in self.session.query(LLMCost).all()]
        }

    def close(self):
        self.session.close()

__all__ = [
    'LLMCost',
    'BudgetExceededError',
    'CostTracker',
]