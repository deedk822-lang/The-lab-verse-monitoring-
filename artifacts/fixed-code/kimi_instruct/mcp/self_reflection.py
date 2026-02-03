import json
import logging
from typing import Dict

class SelfReflection:
    def __init__(self, service):
        self.service = service
        self.log = logging.getLogger("SelfReflection")

    async def refine_plan(self, plan: Dict, context: Dict, attempts: int = 3) -> Dict:
        prompt_template = """
Critique PLAN for gaps/hazards. Output JSON {{refined_plan: object, violations: [str]}}.\nPlan: {{plan}}
Context: {{context}}
"""

        for i in range(attempts):
            resp = await self.service._call_openrouter(
                "tongyi/tongyi-deepresearch-30b",
                prompt_template.format(plan=plan, context=context)
            )
            data = json.loads(resp)
            plan = data.get("refined_plan", plan)
            if not data.get("violations"):
                break
        return plan