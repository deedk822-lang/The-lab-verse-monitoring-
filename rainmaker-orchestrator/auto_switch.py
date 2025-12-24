# rainmaker_orchestrator/auto_switch.py
from datetime import datetime
from typing import Dict, Any
from .orchestrator import RainmakerOrchestrator
import asyncio
import json
import os

class AdaptiveModelRouter:
    """
    Monitors task performance and auto-switches models
    if context explosions or latency issues occur
    """

    def __init__(self, orchestrator: RainmakerOrchestrator):
        self.orchestrator = orchestrator
        self.performance_cache = {}

    async def execute_with_fallback(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Try the routed model, but fallback if it fails
        """
        routing = self.orchestrator.route_task(task)

        try:
            # Attempt primary model
            result = await self.orchestrator.execute_task(task)

            # Cache success metric
            self.performance_cache[routing["model"]] = {
                "success": True,
                "latency": result.get("latency", 0)
            }

            return result

        except Exception as e:
            # Log failure
            print(f"Model {routing['model']} failed: {str(e)}")

            # Fallback to Kimi-Linear for ANY failure
            # (Kimi is the "sovereign" - ultimate fallback)
            print("Falling back to Kimi-Linear Sovereign Engine...")

            fallback_task = task.copy()
            fallback_routing = {
                "model": "kimi-linear-48b",
                "endpoint": self.orchestrator.MODEL_PROFILES["kimi-linear-48b"].model,
                "reason": "Fallback due to primary model failure"
            }

            result = await self.orchestrator._call_kimi(fallback_task, fallback_routing)

            return {
                "routing": fallback_routing,
                "response": result,
                "fallback_from": routing["model"],
                "timestamp": datetime.now().isoformat()
            }

# The magic: Your system now self-heals
async def main():
    orchestrator = RainmakerOrchestrator()
    router = AdaptiveModelRouter(orchestrator)

    # Create a dummy file for the example
    with open("linear_backlog.txt", "w") as f:
        f.write("This is a very long text file." * 10000)

    # Simulate a Linear backlog ingestion task
    task = {
        "type": "ingestion",
        "context": open("./linear_backlog.txt").read(),
        "priority": "high"
    }

    result = await router.execute_with_fallback(task)
    print(json.dumps(result, indent=2))

    # Clean up the dummy file
    os.remove("linear_backlog.txt")

if __name__ == "__main__":
    asyncio.run(main())
