import json
import logging
from typing import Dict


class SelfReflection:
    def __init__(self, service):
        self.service = service
        self.log = logging.getLogger("SelfReflection")

    async def refine_plan(self, plan: dict, context: dict, attempts: int = 3) -> dict:
        # Ensure plan and context are JSON-serializable
        if not isinstance(plan, dict) or not isinstance(context, dict):
            raise ValueError("Plan and context must be dictionaries")

        for i in range(attempts):
            prompt = f"Critique PLAN for gaps/hazards. Output JSON {{refined_plan: object, violations: [str]}}.\nPlan: {json.dumps(plan)}\nContext: {json.dumps(context)}"
            resp = await self.service._call_openrouter("tongyi/tongyi-deepresearch-30b", prompt)
            
            # Ensure response is JSON-parseable
            try:
                data = json.loads(resp)
            except json.JSONDecodeError as e:
                self.log.error(f"Failed to parse OpenRouter response: {e}")
                continue
            
            plan = data.get("refined_plan", plan)
            violations = data.get("violations")
            
            if not violations:
                break
        return plan