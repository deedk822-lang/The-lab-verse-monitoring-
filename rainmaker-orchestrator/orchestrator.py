import requests
import tiktoken
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from prometheus_client import Histogram, Counter
from datetime import datetime
import json
import os
import re
from functools import partial
import sys
import asyncio
from functools import lru_cache
import logging
import time

try:
    from transformers import AutoTokenizer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("Transformers library not available. Token estimation will be less accurate for non-OpenAI models.")

logger = logging.getLogger(__name__)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'vaal-ai-empire')))
from agents.zread_agent import ZreadAgent
from .patent_agent import PatentAgent
from .token_estimator import TokenEstimator

TASK_ROUTING_TIME = Histogram('rainmaker_routing_duration_seconds', 'Time to route task')
TASK_COUNT = Counter('rainmaker_tasks_total', 'Total tasks routed', ['model'])
ERROR_COUNTER = Counter('rainmaker_errors_total', 'Total errors encountered', ['error_type', 'provider'])
LATENCY_HISTOGRAM = Histogram('rainmaker_task_latency_seconds', 'Task processing latency', ['provider', 'task_type'])

@dataclass
class TaskProfile:
    model: str
    context_limit: int
    cost_per_1k: float
    speed: str
    strength: str

class RainmakerOrchestrator:
    def __init__(self):
        self.zread_agent = ZreadAgent()
        self.patent = PatentAgent()
        self.token_estimator = TokenEstimator()

    MODEL_PROFILES = {
        "kimi-linear-48b": TaskProfile(
            model="http://kimi-linear:8000/v1/chat/completions",
            context_limit=1_048_576,
            cost_per_1k=0.10,
            speed="slow",
            strength="ingestion"
        ),
        "deepseek-r1:32b": TaskProfile(
            model="http://ollama:11434/api/chat",
            context_limit=32_768,
            cost_per_1k=0.01,
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
            model="http://localhost:8000",
            context_limit=1048576,
            cost_per_1k=0.01,
            speed="medium",
            strength="private_repo_access"
        )
    }

    TASK_TYPE_PATTERNS = {
        "private_repo_search": re.compile(r'private|repo|github|git', re.I),
        "billing_bug": re.compile(r'billing|stripe|subscription|charge|invoice', re.I),
        "code_audit": re.compile(r'security|vulnerability|xss|injection', re.I)
    }

    def estimate_tokens(self, text: str, model_name: str = "gpt-4") -> int:
        return self.token_estimator.count_tokens(text, model_name)

    def _is_ip_task(self, context: str) -> bool:
        return any(pattern.search(context) for pattern in self.TASK_TYPE_PATTERNS.values())

    def _select_model(self, task: Dict[str, Any], context_size: int) -> tuple[str, str]:
        task_type = task.get("type", "general")

        if self._is_ip_task(task.get("context", "")):
            return "zread", "Private repository access required. Using Zread MCP for deep search/reading."

        if context_size > 100_000:
            return "kimi-linear-48b", f"Context size ({context_size:,} tokens) exceeds Ollama limits"
        elif task_type == "code_debugging":
            return "deepseek-r1:32b", "Reasoning task - using DeepSeek-R1"
        elif task_type == "strategy":
            return "llama4-scout", "Strategy task - Llama4 provides optimal balance"
        elif task_type == "extraction" and context_size < 8_000:
            return "phi4-mini", "Simple extraction - Phi4 for minimal latency"
        elif task_type == "ingestion":
            return "kimi-linear-48b", "Ingestion requires 1M context window"
        else:
            return "llama4-scout", "General task - defaulting to Llama4"

    def route_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        with TASK_ROUTING_TIME.time():
            context_size = self.estimate_tokens(task["context"], "llama4-scout")
            model, reason = self._select_model(task, context_size)
            final_context_size = self.token_estimator.count_tokens(task["context"], model)

            TASK_COUNT.labels(model=model).inc()

            if model == "zread":
                return {
                    "model": model,
                    "provider": "zread",
                    "reason": reason,
                    "estimated_cost": final_context_size * self.MODEL_PROFILES[model].cost_per_1k / 1000,
                    "context_size": final_context_size
                }

            provider = "ollama" if "ollama" in self.MODEL_PROFILES[model].model.lower() else "kimi"

            return {
                "model": model,
                "endpoint": self.MODEL_PROFILES[model].model,
                "provider": provider,
                "reason": reason,
                "estimated_cost": final_context_size * self.MODEL_PROFILES[model].cost_per_1k / 1000,
                "context_size": final_context_size
            }

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        routing = self.route_task(task)
        task_id = task.get("id", "unknown")
        provider = routing.get("provider", "unknown")
        task_subtype = task.get("subtype", "general")
        start_time = asyncio.get_event_loop().time()

        try:
            if task.get("type") == "patent_research":
                subtype = task.get("subtype", "novelty_check")
                if subtype == "novelty_check":
                    from .patent_agent import PatentAgent
                    async with PatentAgent() as patent_agent:
                        patent_data = await patent_agent.novelty_check(task["context"])
                    return await self._synthesize_patent_findings(patent_data, routing)

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

    async def _synthesize_patent_findings(self, patent_data: Dict[str, Any], routing: Dict[str, Any]) -> Dict[str, Any]:
        findings = patent_data.get("findings", {})
        normalized = findings.get("normalized", {})
        patents = normalized.get("patents", [])
        counts = normalized.get("counts", {})

        limited_patents = patents[:25]

        synthesis_prompt = f"""
BASIS: Patent landscape analysis for novelty assessment
SEARCH TERMS: {', '.join(findings.get('key_terms', [])[:5])}
TOTAL UNIQUE PATENTS FOUND: {counts.get('total_unique', 0)}
LENS API RESULTS: {counts.get('lens_success', 0)} successful queries
PATENTSVIEW RESULTS: {counts.get('patentsview_success', 0)} successful queries

RELEVANT PRIOR ART (top {len(limited_patents)} patents by relevance):
{json.dumps(limited_patents, indent=2)}

TASK: Provide a professional novelty assessment including:
1. Overall novelty score (1-10 scale)
2. Key differentiating features vs. existing patents
3. Recommended claim strategy focusing on novel aspects
4. Freedom-to-operate risks and opportunities
5. Most relevant prior art references that must be addressed
6. Specific recommendations for patent application drafting
"""

        synthesis_task = {
            "context": synthesis_prompt,
            "model": routing["model"],
            "subtype": "patent_synthesis"
        }

        return await self.execute_task(synthesis_task)

    async def _call_ollama(self, task: Dict[str, Any], routing: Dict[str, Any]) -> Dict[str, Any]:
        try:
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
        try:
            response = await asyncio.to_thread(
                partial(
                    requests.post,
                    routing["endpoint"],
                    headers={"Authorization": "Bearer EMPTY"},
                    json={
                        "model": "moonshotai/Kimi-Linear-48B-A3B-Instruct",
                        "messages": [{"role": "user", "content": task["context"]}],
                        "max_tokens": 4096,
                        "temperature": 0.3,
                        "top_p": 0.9
                    },
                    timeout=45.0
                )
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise

if __name__ == "__main__":
    orchestrator = RainmakerOrchestrator()

    with open("linear_backlog.txt", "w") as f:
        f.write("This is a very long text file." * 10000)

    task = {
        "type": "ingestion",
        "context": open("./linear_backlog.txt").read(),
        "priority": "high"
    }

    result = orchestrator.route_task(task)
    print(json.dumps(result, indent=2))
    os.remove("linear_backlog.txt")
