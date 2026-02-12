import json
import logging

class ConfidenceEstimator:
    threshold = 0.78

    def __init__(self, service):
        self.service = service
        self.log = logging.getLogger("ConfidenceEstimator")

    async def score_plan(self, plan: dict, context: dict) -> float:
        prompt = f"Rate confidence 0-1 for PLAN success given CONTEXT. Output JSON {{score: float}}.\nPlan: {plan}\nContext: {context}"
        
        try:
            resp = await self.service._call_openrouter("tongyi/tongyi-deepresearch-30b", prompt)
            data = json.loads(resp)
            if "score" in data:
                return float(data["score"])
            else:
                raise ValueError("No 'score' key found in the response.")
        except Exception as e:
            self.log.warning("LLM score failed %s – heuristic fallback", e)
            
            # Heuristic fallback logic
            heuristic = min(len(plan.get("steps", [])) / 5, 1.0) * 0.6
            
            if "risk" in context:
                heuristic -= context["risk"] * 0.3
            
            return max(0.0, min(1.0, heuristic))

# Example usage
if __name__ == "__main__":
    # Initialize the service and confidence estimator
    service = ...  # Assume this is initialized elsewhere
    estimator = ConfidenceEstimator(service)
    
    # Define some sample plan and context
    plan = {
        "steps": [
            {"description": "Step 1", "probability": 0.8},
            {"description": "Step 2", "probability": 0.7}
        ]
    }
    context = {
        "risk": 0.1
    }
    
    # Score the plan
    confidence = estimator.score_plan(plan, context)
    print(f"Estimated confidence: {confidence}")