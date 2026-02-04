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
            return float(data.get("score", 0.0))
        except Exception as e:
            self.log.warning("LLM score failed %s – heuristic fallback", e)
            heuristic = min(len(plan.get("steps", [])) / 5, 1.0) * 0.6
            if "risk" in context:
                heuristic -= context["risk"] * 0.3
            return max(0.0, min(1.0, heuristic))

# Example usage
if __name__ == "__main__":
    from transformers import AutoTokenizer, AutoModelForCausalLM

    tokenizer = AutoTokenizer.from_pretrained("tongyi/tongyi-deepresearch-30b")
    model = AutoModelForCausalLM.from_pretrained("tongyi/tongyi-deepresearch-30b")

    class OpenRouterService:
        async def _call_openrouter(self, model_name, prompt):
            # Simulate a call to the Open Router API
            return "{'score': 0.85}"

    estimator = ConfidenceEstimator(OpenRouterService())
    plan = {"steps": [{"instruction": "Do something", "action": "execute"}]}
    context = {"risk": 1.2}
    confidence_score = estimator.score_plan(plan, context)
    print(f"Confidence Score: {confidence_score}")