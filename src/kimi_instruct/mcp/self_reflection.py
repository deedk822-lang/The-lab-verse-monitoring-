import json
import logging


class SelfReflection:
    def __init__(self, service):
        self.service = service
        self.log = logging.getLogger("SelfReflection")

    async def refine_plan(self, plan: dict, context: dict, attempts: int = 3) -> dict:
        for _i in range(attempts):
            prompt = f"Critique PLAN for gaps/hazards. Output JSON {{refined_plan: object, violations: [str]}}.\nPlan: {json.dumps(plan)}\nContext: {json.dumps(context)}"
            resp = await self.service._call_openrouter(
                "tongyi/tongyi-deepresearch-30b", prompt
            )
            data = json.loads(resp)
            plan = data.get("refined_plan", plan)
            if not data.get("violations"):
                break
        return plan
