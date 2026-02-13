import json
import logging
from typing import Dict

class SelfReflection:
    def __init__(self, service):
        self.service = service
        self.log = logging.getLogger("SelfReflection")

    async def refine_plan(self, plan: dict, context: dict, attempts: int = 3) -> dict:
        # Sanitize the plan and context to prevent injection attacks
        sanitized_plan = json.dumps(plan)
        sanitized_context = json.dumps(context)

        for i in range(attempts):
            prompt = f"Critique PLAN for gaps/hazards. Output JSON {{refined_plan: object, violations: [str]}}.\nPlan: {sanitized_plan}\nContext: {sanitized_context}"
            resp = await self.service._call_openrouter("tongyi/tongyi-deepresearch-30b", prompt)
            data = json.loads(resp)

            plan = data.get("refined_plan", plan)
            if not data.get("violations"):
                break

        return plan