import json, logging
from typing import Dict


class SelfReflection:
    def __init__(self, service):
        self.service = service
        self.log = logging.getLogger("SelfReflection")
        self.log.setLevel(logging.DEBUG)

    async def refine_plan(self, plan: Dict, context: Dict, attempts: int = 3) -> Dict:
        for i in range(attempts):
            prompt = f"Critique PLAN for gaps/hazards. Output JSON {{refined_plan: object, violations: [str]}}.\nPlan: {json.dumps(plan)}\nContext: {json.dumps(context)}"
            resp = await self.service._call_openrouter(
                "tongyi/tongyi-deepresearch-30b", prompt
            )
            data = json.loads(resp)
            plan = data.get("refined_plan", plan)
            violations = data.get("violations")
            if not violations:
                break
        return plan

import json, logging
from typing import Dict


class SelfReflection:
    def __init__(self, service):
        self.service = service
        self.log = logging.getLogger("SelfReflection")
        self.log.setLevel(logging.DEBUG)

    async def refine_plan(self, plan: Dict, context: Dict, attempts: int = 3) -> Dict:
        for i in range(attempts):
            prompt = f"Critique PLAN for gaps/hazards. Output JSON {{refined_plan: object, violations: [str]}}.\nPlan: {json.dumps(plan)}\nContext: {json.dumps(context)}"
            resp = await self.service._call_openrouter(
                "tongyi/tongyi-deepresearch-30b", prompt
            )
            data = json.loads(resp)
            plan, violations = data["refined_plan"], data["violations"]
            if not violations:
                break
        return plan

import json, logging
from typing import Dict


class SelfReflection:
    def __init__(self, service):
        self.service = service
        self.log = logging.getLogger("SelfReflection")
        self.log.setLevel(logging.DEBUG)

    async def refine_plan(self, plan: Dict, context: Dict, attempts: int = 3) -> Dict:
        for i in range(attempts):
            prompt = f"Critique PLAN for gaps/hazards. Output JSON {{refined_plan: object, violations: [str]}}.\nPlan: {json.dumps(plan)}\nContext: {json.dumps(context)}"
            try:
                resp = await self.service._call_openrouter(
                    "tongyi/tongyi-deepresearch-30b", prompt
                )
                data = json.loads(resp)
                plan, violations = data["refined_plan"], data["violations"]
            except Exception as e:
                self.log.error(f"Failed to refine plan: {e}")
                return plan  # or raise an exception if needed
            if not violations:
                break
        return plan
