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
            # Use parameterized query to prevent SQL injection
            params = {
                "plan": json.dumps(plan),
                "context": json.dumps(context)
            }
            resp = await self.service._call_openrouter(
                "tongyi/tongyi-deepresearch-30b", prompt, **params
            )
            data = json.loads(resp)
            return float(data.get("score", 0.0))
        except Exception as e:
            # Log the exception details for debugging
            self.log.error("LLM score failed %s – heuristic fallback", e)
            heuristic = min(len(plan.get("steps", [])) / 5, 1.0) * 0.6
            if "risk" in context:
                heuristic -= context["risk"] * 0.3
            return max(0.0, min(1.0, heuristic))
