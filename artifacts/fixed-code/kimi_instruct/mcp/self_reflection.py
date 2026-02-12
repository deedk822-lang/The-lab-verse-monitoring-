import json
import logging


class SelfReflection:
    def __init__(self, service):
        self.service = service
        self.log = logging.getLogger("SelfReflection")

    async def refine_plan(self, plan: dict, context: dict, attempts: int = 3) -> dict:
        # Validate input data
        if not isinstance(plan, dict) or not isinstance(context, dict):
            raise ValueError("Input must be a dictionary")
        
        for i in range(attempts):
            try:
                prompt = f"Critique PLAN for gaps/hazards. Output JSON {{refined_plan: object, violations: [str]}}.\nPlan: {json.dumps(plan)}\nContext: {json.dumps(context)}"
                resp = await self.service._call_openrouter("tongyi/tongyi-deepresearch-30b", prompt)
                
                # Parse the response
                data = json.loads(resp)
                
                # Check for violations
                if not data.get("violations"):
                    break
                
            except Exception as e:
                logging.error(f"Error during refinement attempt {i+1}: {e}")
                if i + 1 < attempts - 1:
                    continue
                else:
                    raise

        return plan