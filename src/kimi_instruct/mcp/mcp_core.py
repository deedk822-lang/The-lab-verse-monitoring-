import logging
from typing import Dict, Tuple
from .confidence import ConfidenceEstimator
from .self_reflection import SelfReflection

class MCPCore:
    def __init__(self, service):
        self.service = service
        self.log = logging.getLogger("MCPCore")
        self.conf = ConfidenceEstimator(service)
        self.refl = SelfReflection(service)

    async def validate_and_refine(self, goal: str, plan: Dict, context: Dict) -> Tuple[Dict, bool]:
        score = await self.conf.score_plan(plan, context)
        self.log.info("Plan confidence for %s: %.3f", goal, score)
        if score < self.conf.threshold:
            plan = await self.refl.refine_plan(plan, context)
            return plan, True
        return plan, False