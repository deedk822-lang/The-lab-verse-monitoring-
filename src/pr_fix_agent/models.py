"""
Model Selection logic
Issue Fixed: #21: Budget-aware model selection
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ModelSpec:
    """Model specification"""
    name: str
    provider: str  # ollama, openai, anthropic
    cost_per_million_tokens: float
    quality_score: int  # 1-10
    speed_score: int  # 1-10
    context_window: int
    specialization: str  # reasoning, coding, general


class ModelSelector:
    """
    Select best model for task and budget

    Features:
    - Cost-aware selection
    - Quality optimization
    - Fallback chains
    - Provider diversity
    """

    MODELS = {
        "reasoning": [
            ModelSpec(
                name="deepseek-r1:14b",
                provider="ollama",
                cost_per_million_tokens=0.0,
                quality_score=9,
                speed_score=6,
                context_window=32000,
                specialization="reasoning"
            ),
            ModelSpec(
                name="qwen2.5:32b",
                provider="ollama",
                cost_per_million_tokens=0.0,
                quality_score=8,
                speed_score=7,
                context_window=32000,
                specialization="reasoning"
            ),
            ModelSpec(
                name="o1-preview",
                provider="openai",
                cost_per_million_tokens=15.0,
                quality_score=10,
                speed_score=4,
                context_window=128000,
                specialization="reasoning"
            ),
        ],
        "coding": [
            ModelSpec(
                name="qwen2.5-coder:32b",
                provider="ollama",
                cost_per_million_tokens=0.0,
                quality_score=9,
                speed_score=8,
                context_window=32000,
                specialization="coding"
            ),
            ModelSpec(
                name="codellama:34b",
                provider="ollama",
                cost_per_million_tokens=0.0,
                quality_score=7,
                speed_score=9,
                context_window=16000,
                specialization="coding"
            ),
            ModelSpec(
                name="claude-3-5-sonnet",
                provider="anthropic",
                cost_per_million_tokens=3.0,
                quality_score=10,
                speed_score=8,
                context_window=200000,
                specialization="coding"
            ),
        ]
    }

    def select_model(
        self,
        task: str,
        budget_remaining: float = 0.0,
        prefer_free: bool = True,
        min_quality: int = 7
    ) -> Optional[ModelSpec]:
        """
        Select best model for task

        Args:
            task: "reasoning" or "coding"
            budget_remaining: Available budget in dollars
            prefer_free: Prefer free (Ollama) models
            min_quality: Minimum quality score required

        Returns:
            Best model matching criteria, or None
        """
        candidates = self.MODELS.get(task, [])

        # Filter by budget
        affordable = [
            m for m in candidates
            if m.cost_per_million_tokens <= budget_remaining or m.cost_per_million_tokens == 0.0
        ]

        if not affordable:
            return None

        # Filter by quality
        quality_filtered = [m for m in affordable if m.quality_score >= min_quality]

        if not quality_filtered:
            quality_filtered = affordable  # Relax quality if needed

        # Sort by preference
        if prefer_free:
            # Free models first, then by quality
            sorted_models = sorted(
                quality_filtered,
                key=lambda m: (m.cost_per_million_tokens > 0, -m.quality_score)
            )
        else:
            # Highest quality first
            sorted_models = sorted(
                quality_filtered,
                key=lambda m: -m.quality_score
            )

        return sorted_models[0] if sorted_models else None

    def get_fallback_chain(self, task: str) -> List[ModelSpec]:
        """
        Get fallback chain for task

        Returns models in order of preference (free first)
        """
        candidates = self.MODELS.get(task, [])

        # Sort: free models first, then by quality
        return sorted(
            candidates,
            key=lambda m: (m.cost_per_million_tokens > 0, -m.quality_score)
        )
