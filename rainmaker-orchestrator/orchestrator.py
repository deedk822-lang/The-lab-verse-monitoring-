# rainmaker_orchestrator/orchestrator.py
import requests
import tiktoken
from typing import Dict, Any
from dataclasses import dataclass
from prometheus_client import Histogram, Counter
from datetime import datetime
import json
import os

# Metrics for monitoring
TASK_ROUTING_TIME = Histogram('rainmaker_routing_duration_seconds', 'Time to route task')
TASK_COUNT = Counter('rainmaker_tasks_total', 'Total tasks routed', ['model'])
TOKEN_ESTIMATOR = tiktoken.encoding_for_model("gpt-4")

@dataclass
class TaskProfile:
    """Defines the cost/quality tradeoff for each model"""
    model: str
    context_limit: int
    cost_per_1k: float
    speed: str  # "fast", "medium", "slow"
    strength: str  # "reasoning", "general", "ingestion"

class RainmakerOrchestrator:
    """
    Routes tasks between Kimi-Linear (1M context) and Ollama models
    based on actual requirements, not just "use the biggest model"
    """
<<<<<<< HEAD

=======

>>>>>>> c00699664d3818edf437bf12f56f434451084e1b
    MODEL_PROFILES = {
        "kimi-linear-48b": TaskProfile(
            model="http://kimi-linear:8000/v1/chat/completions",
            context_limit=1_048_576,
            cost_per_1k=0.10,  # Your bulk Azure cost
            speed="slow",
            strength="ingestion"
        ),
        "deepseek-r1:32b": TaskProfile(
            model="http://ollama:11434/api/chat",
            context_limit=32_768,
            cost_per_1k=0.01,  # Local GPU cost
            speed="medium",
            strength="reasoning"
        ),
        "llama4-scout": TaskProfile(
            model="http://ollama:11434/api/chat",
            context_limit=32_768,
            cost_per_1k=0.005,
            speed="fast",
            strength="general"
        ),
        "phi4-mini": TaskProfile(
            model="http://ollama:11434/api/chat",
            context_limit=16_384,
            cost_per_1k=0.001,
            speed="fastest",
            strength="simple"
        )
    }
<<<<<<< HEAD

    def estimate_tokens(self, text: str) -> int:
        """Quick token estimation without full encoding"""
        return len(TOKEN_ESTIMATOR.encode(text))

=======

    def estimate_tokens(self, text: str) -> int:
        """Quick token estimation without full encoding"""
        return len(TOKEN_ESTIMATOR.encode(text))

>>>>>>> c00699664d3818edf437bf12f56f434451084e1b
    def route_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        The brain: decide which model to use
        task = {
            "type": "code_debugging"|"strategy"|"ingestion"|"extraction",
            "context": "full text or code",
            "priority": "high"|"low"
        }
        """
        with TASK_ROUTING_TIME.time():
            context_size = self.estimate_tokens(task["context"])
            task_type = task.get("type", "general")
<<<<<<< HEAD

=======

>>>>>>> c00699664d3818edf437bf12f56f434451084e1b
            # Routing logic based on actual facts
            if context_size > 100_000:
                # Only Kimi can handle this
                model = "kimi-linear-48b"
                reason = f"Context size ({context_size:,} tokens) exceeds Ollama limits"
<<<<<<< HEAD

=======

>>>>>>> c00699664d3818edf437bf12f56f434451084e1b
            elif task_type == "code_debugging":
                # DeepSeek-R1 for reasoning
                model = "deepseek-r1:32b"
                reason = "Reasoning task - using DeepSeek-R1"
<<<<<<< HEAD

=======

>>>>>>> c00699664d3818edf437bf12f56f434451084e1b
            elif task_type == "strategy":
                # Llama4 for balanced quality/speed
                model = "llama4-scout"
                reason = "Strategy task - Llama4 provides optimal balance"
<<<<<<< HEAD

=======

>>>>>>> c00699664d3818edf437bf12f56f434451084e1b
            elif task_type == "extraction" and context_size < 8_000:
                # Phi4 for speed on simple tasks
                model = "phi4-mini"
                reason = "Simple extraction - Phi4 for minimal latency"
<<<<<<< HEAD

=======

>>>>>>> c00699664d3818edf437bf12f56f434451084e1b
            elif task_type == "ingestion":
                # Kimi for massive document processing
                model = "kimi-linear-48b"
                reason = "Ingestion requires 1M context window"
<<<<<<< HEAD

=======

>>>>>>> c00699664d3818edf437bf12f56f434451084e1b
            else:
                # Default to Llama4
                model = "llama4-scout"
                reason = "General task - defaulting to Llama4"
<<<<<<< HEAD

            TASK_COUNT.labels(model=model).inc()

=======

            TASK_COUNT.labels(model=model).inc()

>>>>>>> c00699664d3818edf437bf12f56f434451084e1b
            return {
                "model": model,
                "endpoint": self.MODEL_PROFILES[model].model,
                "reason": reason,
                "estimated_cost": context_size * self.MODEL_PROFILES[model].cost_per_1k / 1000,
                "context_size": context_size
            }
<<<<<<< HEAD

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Route and execute in one call"""
        routing = self.route_task(task)

=======

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Route and execute in one call"""
        routing = self.route_task(task)

>>>>>>> c00699664d3818edf437bf12f56f434451084e1b
        # Call the appropriate model
        if "ollama" in routing["model"]:
            response = await self._call_ollama(task, routing)
        else:
            response = await self._call_kimi(task, routing)
<<<<<<< HEAD

=======

>>>>>>> c00699664d3818edf437bf12f56f434451084e1b
        return {
            "routing": routing,
            "response": response,
            "timestamp": datetime.now().isoformat()
        }
<<<<<<< HEAD

=======

>>>>>>> c00699664d3818edf437bf12f56f434451084e1b
    async def _call_ollama(self, task: Dict[str, Any], routing: Dict[str, Any]) -> Dict[str, Any]:
        """Call Ollama API"""
        response = requests.post(
            routing["endpoint"],
            json={
                "model": routing["model"],
                "messages": [{"role": "user", "content": task["context"]}],
                "stream": False
            }
        )
        return response.json()
<<<<<<< HEAD

=======

>>>>>>> c00699664d3818edf437bf12f56f434451084e1b
    async def _call_kimi(self, task: Dict[str, Any], routing: Dict[str, Any]) -> Dict[str, Any]:
        """Call Kimi-Linear via OpenAI-compatible API"""
        response = requests.post(
            routing["endpoint"],
            headers={"Authorization": "Bearer EMPTY"},
            json={
                "model": "moonshotai/Kimi-Linear-48B-A3B-Instruct",
                "messages": [{"role": "user", "content": task["context"]}],
                "max_tokens": 2000
            }
        )
        return response.json()

# Usage example
if __name__ == "__main__":
    orchestrator = RainmakerOrchestrator()
<<<<<<< HEAD

=======

>>>>>>> c00699664d3818edf437bf12f56f434451084e1b
    # Create a dummy file for the example
    with open("linear_backlog.txt", "w") as f:
        f.write("This is a very long text file." * 10000)

    # Simulate a Linear backlog ingestion task
    task = {
        "type": "ingestion",
        "context": open("./linear_backlog.txt").read(),  # 500K tokens
        "priority": "high"
    }
<<<<<<< HEAD

    result = orchestrator.route_task(task)
    print(json.dumps(result, indent=2))
    # Will route to kimi-linear-48b due to context size

=======

    result = orchestrator.route_task(task)
    print(json.dumps(result, indent=2))
    # Will route to kimi-linear-48b due to context size

>>>>>>> c00699664d3818edf437bf12f56f434451084e1b
    # Clean up the dummy file
    os.remove("linear_backlog.txt")
