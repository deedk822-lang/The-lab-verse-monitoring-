import json
import logging
from typing import Dict

class ConfidenceEstimator:
    threshold = 0.78

    def __init__(self, service):
        self.service = service
        self.log = logging.getLogger("ConfidenceEstimator")

    async def score_plan(self, plan: Dict, context: Dict) -> float:
        prompt = f"Rate confidence 0-1 for PLAN success given CONTEXT. Output JSON {{score: float}}.\nPlan: {json.dumps(plan)}\nContext: {json.dumps(context)}"
        try:
            resp = await self.service._call_openrouter(
                "tongyi/tongyi-deepresearch-30b", prompt
            )
            data = json.loads(resp)
            if not isinstance(data, dict) or "score" not in data or not isinstance(data["score"], float):
                self.log.warning("Invalid JSON response from LLM")
                return self.heuristic_score(plan, context)
        except Exception as e:
            self.log.error(f"LLM score failed {e}")
            return self.heuristic_score(plan, context)

    def heuristic_score(self, plan: dict, context: dict) -> float:
        # Implement the heuristic scoring logic
        heuristic = min(len(plan.get("steps", [])) / 5, 1.0) * 0.6
        if "risk" in context:
            heuristic -= context["risk"] * 0.3
        return max(0.0, min(1.0, heuristic))