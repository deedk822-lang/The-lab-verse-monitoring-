# rainmaker_orchestrator/orchestrator.py
import requests
import tiktoken
from typing import Dict, Any
from dataclasses import dataclass
from prometheus_client import Histogram, Counter
from datetime import datetime
import json
import os
import re
from functools import partial
import sys
import asyncio

# Add vaal-ai-empire to path to import ZreadAgent
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'vaal-ai-empire')))
from agents.zread_agent import ZreadAgent
from .patent_agent import PatentAgent


# Metrics for monitoring
TASK_ROUTING_TIME = Histogram('rainmaker_routing_duration_seconds', 'Time to route task')
TASK_COUNT = Counter('rainmaker_tasks_total', 'Total tasks routed', ['provider', 'task_type'])
ERROR_COUNTER = Counter('rainmaker_errors_total', 'Total errors encountered', ['error_type', 'provider'])
LATENCY_HISTOGRAM = Histogram('rainmaker_task_latency_seconds', 'Task processing latency', ['provider', 'task_type'])
try:
    TOKEN_ESTIMATOR = tiktoken.encoding_for_model("gpt-4")
except KeyError:
    TOKEN_ESTIMATOR = tiktoken.get_encoding("cl100k_base")

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
    def __init__(self):
        self.zread_agent = ZreadAgent()
        self.patent = PatentAgent()

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
        ),
        "zread": TaskProfile(
            model="http://localhost:8000", # Or your Zread API URL
            context_limit=1048576, # Zread needs full context
            cost_per_1k=0.01, # Check Zread pricing
            speed="medium",
            strength="private_repo_access"
        )
    }

    TASK_TYPE_PATTERNS = {
        "private_repo_search": re.compile(r'private|repo|github|git', re.I),
        "billing_bug": re.compile(r'billing|stripe|subscription|charge|invoice', re.I),
        "code_audit": re.compile(r'security|vulnerability|xss|injection', re.I)
    }

    def estimate_tokens(self, text: str) -> int:
        """Quick token estimation without full encoding"""
        return len(TOKEN_ESTIMATOR.encode(text))

    def _is_ip_task(self, context: str) -> bool:
        """Check if the task is related to private repo search"""
        return any(pattern.search(context) for pattern in self.TASK_TYPE_PATTERNS.values())

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

            # Check if it's a private repo task
            if self._is_ip_task(task.get("context", "")):
                model = "zread" # Force Zread
                reason = "Private repository access required. Using Zread MCP for deep search/reading."

                return {
                    "model": model,
                    "provider": "zread",
                    "reason": reason,
                    "estimated_cost": context_size * self.MODEL_PROFILES[model].cost_per_1k / 1000,
                    "context_size": context_size
                }

            # Routing logic based on actual facts
            if context_size > 100_000:
                # Only Kimi can handle this
                model = "kimi-linear-48b"
                reason = f"Context size ({context_size:,} tokens) exceeds Ollama limits"

            elif task_type == "code_debugging":
                # DeepSeek-R1 for reasoning
                model = "deepseek-r1:32b"
                reason = "Reasoning task - using DeepSeek-R1"

            elif task_type == "strategy":
                # Llama4 for balanced quality/speed
                model = "llama4-scout"
                reason = "Strategy task - Llama4 provides optimal balance"

            elif task_type == "extraction" and context_size < 8_000:
                # Phi4 for speed on simple tasks
                model = "phi4-mini"
                reason = "Simple extraction - Phi4 for minimal latency"

            elif task_type == "ingestion":
                # Kimi for massive document processing
                model = "kimi-linear-48b"
                reason = "Ingestion requires 1M context window"

            else:
                # Default to Llama4
                model = "llama4-scout"
                reason = "General task - defaulting to Llama4"

            provider = "ollama" if "ollama" in self.MODEL_PROFILES[model].model.lower() else "kimi"
            TASK_COUNT.labels(provider=provider, task_type=task.get("type", "general")).inc()

            return {
                "model": model,
                "endpoint": self.MODEL_PROFILES[model].model,
                "provider": provider,
                "reason": reason,
                "estimated_cost": context_size * self.MODEL_PROFILES[model].cost_per_1k / 1000,
                "context_size": context_size
            }

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Route and execute in one call"""
        routing = self.route_task(task)
        task_id = task.get("id", "unknown")
        provider = routing.get("provider", "unknown")
        task_subtype = task.get("subtype", "general")
        start_time = asyncio.get_event_loop().time()

        try:
            # Add patent research routing
            if task.get("type") == "patent_research":
                subtype = task.get("subtype", "novelty_check")
                if subtype == "novelty_check":
                    patent_data = await self.patent.novelty_check(task["context"])
                    findings = patent_data.get("findings", patent_data)
                    synthesis_prompt = f"""
                    Based on this patent landscape analysis:
                    {json.dumps(findings, indent=2)}

                    Provide a professional novelty assessment. Include:
                    1. Novelty score (1-10)
                    2. Key differentiators vs. existing patents
                    3. Recommended claim strategy
                    4. Risks and opportunities
                    """
                    synthesis_task = task.copy()
                    synthesis_task["context"] = synthesis_prompt
                    lm_response = await self._call_kimi(synthesis_task, routing)
                    synthesis = lm_response["choices"][0]["message"]["content"]
                    return {
                        "status": "success",
                        "task_id": task_id,
                        "type": "patent_research",
                        "patent_data": patent_data,
                        "expert_assessment": synthesis
                    }

            # Call the appropriate model or agent
            if routing.get("provider") == "zread":
                repo_url = task.get("repo_url", "https://github.com/example/repo")
                query = task.get("context", "")
                response = await asyncio.to_thread(self.zread_agent.search_repo, repo_url, query)
            elif routing.get("provider") == "ollama":
                response = await self._call_ollama(task, routing)
            else:
                response = await self._call_kimi(task, routing)

            return {
                "routing": routing,
                "response": response,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            error_type = type(e).__name__
            ERROR_COUNTER.labels(error_type=error_type, provider=provider).inc()
            raise
        finally:
            latency = asyncio.get_event_loop().time() - start_time
            LATENCY_HISTOGRAM.labels(provider=provider, task_type=task_subtype).observe(latency)

    async def _call_ollama(self, task: Dict[str, Any], routing: Dict[str, Any]) -> Dict[str, Any]:
        """Make async Ollama API call without blocking event loop"""
        try:
            # Critical fix: run blocking requests in thread pool
            response = await asyncio.to_thread(
                partial(
                    requests.post,
                    routing["endpoint"],
                    json={
                        "model": routing["model"],
                        "messages": [{"role": "user", "content": task["context"]}],
                        "stream": False
                    },
                    timeout=30.0
                )
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise

    async def _call_kimi(self, task: Dict[str, Any], routing: Dict[str, Any]) -> Dict[str, Any]:
        """Make async Kimi API call without blocking event loop"""
        try:
            # Critical fix: run blocking requests in thread pool
            response = await asyncio.to_thread(
                partial(
                    requests.post,
                    routing["endpoint"],
                    headers={"Authorization": "Bearer EMPTY"},
                    json={
                        "model": "moonshotai/Kimi-Linear-48B-A3B-Instruct",
                        "messages": [{"role": "user", "content": task["context"]}],
                        "max_tokens": 2000,
                        "temperature": 0.7
                    },
                    timeout=45.0
                )
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise

# Usage example
if __name__ == "__main__":
    orchestrator = RainmakerOrchestrator()

    # Create a dummy file for the example
    with open("linear_backlog.txt", "w") as f:
        f.write("This is a very long text file." * 10000)

    # Simulate a Linear backlog ingestion task
    task = {
        "type": "ingestion",
        "context": open("./linear_backlog.txt").read(),  # 500K tokens
        "priority": "high"
    }

    result = orchestrator.route_task(task)
    print(json.dumps(result, indent=2))
    # Will route to kimi-linear-48b due to context size

    # Clean up the dummy file
    os.remove("linear_backlog.txt")
