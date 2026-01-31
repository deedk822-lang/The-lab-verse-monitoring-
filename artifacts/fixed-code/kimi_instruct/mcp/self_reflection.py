import json
import logging
from typing import Dict


class SelfReflection:
    def __init__(self, service):
        self.service = service
        self.log = logging.getLogger("SelfReflection")

    async def refine_plan(self, plan: Dict, context: Dict, attempts: int = 3) -> Dict:
        try:
            # Sanitize the inputs to prevent JSON injection attacks
            plan_json = json.dumps(plan)
            context_json = json.dumps(context)

            for i in range(attempts):
                prompt = f"Critique PLAN for gaps/hazards. Output JSON {{refined_plan: object, violations: [str]}}.\nPlan: {plan_json}\nContext: {context_json}"
                resp = await self.service._call_openrouter(
                    "tongyi/tongyi-deepresearch-30b", prompt
                )
                data = json.loads(resp)
                plan = data.get("refined_plan", plan)
                if not data.get("violations"):
                    break
        except (json.JSONDecodeError, ValueError) as e:
            self.log.error(f"Error while processing the response: {e}")
            return None  # Return None or handle the error appropriately