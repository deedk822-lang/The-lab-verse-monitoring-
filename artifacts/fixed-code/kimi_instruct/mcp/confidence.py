import json
import logging

class ConfidenceEstimator:
    threshold = 0.78

    def __init__(self, service):
        self.service = service
        self.log = logging.getLogger("ConfidenceEstimator")

    async def score_plan(self, plan: dict, context: dict) -> float:
        prompt = f"Rate confidence 0-1 for PLAN success given CONTEXT. Output JSON {{score: float}}.\nPlan: {json.dumps(plan)}\nContext: {json.dumps(context)}"
        
        try:
            resp = await self.service._call_openrouter(
                "tongyi/tongyi-deepresearch-30b", prompt
            )
            data = json.loads(resp)
            return float(data.get("score", 0.0))
        except Exception as e:
            self.log.error(f"LLM score failed {e}")
            raise  # Re-raise the exception for further handling

    async def heuristic_score(self, plan: dict, context: dict) -> float:
        steps = plan.get("steps", [])
        if steps:
            heuristic = len(steps) / 5
        else:
            heuristic = 0.0
        
        if "risk" in context:
            heuristic -= context["risk"] * 0.3
        
        return max(0.0, min(1.0, heuristic))

    async def score_plan_with_heuristic(self, plan: dict, context: dict) -> float:
        try:
            confidence_score = await self.score_plan(plan, context)
            if confidence_score < self.threshold:
                heuristic_score = await self.heuristic_score(plan, context)
                confidence_score = min(confidence_score + heuristic_score, 1.0)
        
        except Exception as e:
            self.log.error(f"Failed to score plan: {e}")
            confidence_score = 0.0
        
        return confidence_score