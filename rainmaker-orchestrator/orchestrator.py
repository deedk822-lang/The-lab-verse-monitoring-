# rainmaker_orchestrator/orchestrator.py
import requests
import tiktoken
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from prometheus_client import Histogram, Counter
from datetime import datetime
import json
import os
import re
import sys
import asyncio
from functools import lru_cache
import logging
import time

# Add these imports at the top of orchestrator.py
try:
    from transformers import AutoTokenizer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("Transformers library not available. Token estimation will be less accurate for non-OpenAI models.")

logger = logging.getLogger(__name__)


# Add vaal-ai-empire to path to import ZreadAgent
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'vaal-ai-empire')))
from agents.zread_agent import ZreadAgent
from rainmaker_orchestrator.patent_agent import PatentAgent


# Metrics for monitoring
TASK_ROUTING_TIME = Histogram('rainmaker_routing_duration_seconds', 'Time to route task')
TASK_COUNT = Counter('rainmaker_tasks_total', 'Total tasks routed', ['model'])

class TokenEstimator:
    """
    Robust token estimator with fallbacks for multiple model families.
    Handles OpenAI models (tiktoken) and open-source models (transformers).
    """

    # Model family to tokenizer mapping
    MODEL_FAMILY_MAPPING = {
        # OpenAI models
        "gpt-4": "cl100k_base",
        "gpt-3.5": "cl100k_base",
        "gpt-3": "p50k_base",

        # Meta Llama family
        "llama": "meta-llama/Llama-2-7b-hf",
        "llama2": "meta-llama/Llama-2-7b-hf",
        "llama3": "meta-llama/Meta-Llama-3-8B",
        "llama4": "meta-llama/Meta-Llama-3-8B",  # Fallback for llama4-scout

        # DeepSeek family
        "deepseek": "deepseek-ai/deepseek-coder-1.3b-base",
        "deepseek-r1": "deepseek-ai/deepseek-coder-1.3b-base",

        # Microsoft Phi family
        "phi": "microsoft/phi-2",
        "phi4": "microsoft/phi-2",  # Fallback for phi4-mini

        # Mistral family (common fallback)
        "mistral": "mistralai/Mistral-7B-v0.1",
    }

    def __init__(self):
        self.tiktoken_encodings = {}
        self.transformers_tokenizers = {}
        self.fallback_encoder = self._get_safe_fallback_encoder()
        self.last_tokenizer_load = {}

    @lru_cache(maxsize=32)
    def get_tokenizer_for_model(self, model_name: str):
        """
        Get appropriate tokenizer for a model with intelligent fallbacks.
        Uses LRU cache to avoid repeated initialization.
        """
        model_name_lower = model_name.lower()

        try:
            # First try: direct model mapping
            for family, tokenizer_name in self.MODEL_FAMILY_MAPPING.items():
                if family in model_name_lower:
                    if tokenizer_name.startswith(("cl100k_base", "p50k_base", "r50k_base")):
                        return self._get_tiktoken_encoding(tokenizer_name)
                    else:
                        return self._get_transformers_tokenizer(tokenizer_name, model_name)

            # Second try: OpenAI model detection
            try:
                return tiktoken.encoding_for_model(model_name)
            except KeyError:
                pass

            # Third try: heuristic matching
            if any(x in model_name_lower for x in ["gpt-4", "gpt-3.5", "chatgpt"]):
                return self._get_tiktoken_encoding("cl100k_base")
            elif any(x in model_name_lower for x in ["llama", "llama2", "llama3", "llama4"]):
                return self._get_transformers_tokenizer("meta-llama/Meta-Llama-3-8B", model_name)
            elif "deepseek" in model_name_lower:
                return self._get_transformers_tokenizer("deepseek-ai/deepseek-coder-1.3b-base", model_name)
            elif "phi" in model_name_lower:
                return self._get_transformers_tokenizer("microsoft/phi-2", model_name)
            elif "mistral" in model_name_lower or "mixtral" in model_name_lower:
                return self._get_transformers_tokenizer("mistralai/Mistral-7B-v0.1", model_name)

            # Fourth try: generic fallbacks
            logger.warning(f"No specific tokenizer found for model '{model_name}'. Using cl100k_base fallback.")
            return self._get_tiktoken_encoding("cl100k_base")

        except Exception as e:
            logger.error(f"Error getting tokenizer for model '{model_name}': {str(e)}")
            return self.fallback_encoder

    def count_tokens(self, text: str, model_name: str) -> int:
        """
        Count tokens in text for a specific model with robust fallbacks.
        """
        if not text or not isinstance(text, str):
            return 0

        tokenizer = self.get_tokenizer_for_model(model_name)

        try:
            # Handle tiktoken encodings
            if hasattr(tokenizer, "encode"):
                return len(tokenizer.encode(text))

            # Handle transformers tokenizers
            elif hasattr(tokenizer, "tokenize"):
                return len(tokenizer.tokenize(text))

            elif hasattr(tokenizer, "__call__"):
                # For tokenizers that use __call__ directly
                return len(tokenizer(text)["input_ids"])

            else:
                logger.warning(f"Unknown tokenizer type for model '{model_name}'. Using fallback estimation.")
                return self._fallback_token_count(text)

        except Exception as e:
            logger.error(f"Error counting tokens for model '{model_name}': {str(e)}")
            return self._fallback_token_count(text)

    def _get_tiktoken_encoding(self, encoding_name: str):
        """Get or create a tiktoken encoding with caching."""
        if encoding_name not in self.tiktoken_encodings:
            try:
                self.tiktoken_encodings[encoding_name] = tiktoken.get_encoding(encoding_name)
            except Exception as e:
                logger.error(f"Failed to get tiktoken encoding '{encoding_name}': {str(e)}")
                self.tiktoken_encodings[encoding_name] = self.fallback_encoder
        return self.tiktoken_encodings[encoding_name]

    def _get_transformers_tokenizer(self, tokenizer_name: str, model_name: str):
        """Get or create a transformers tokenizer with caching and fallbacks."""
        if not TRANSFORMERS_AVAILABLE:
            logger.warning(f"Transformers not available. Using tiktoken for model '{model_name}'.")
            return self._get_tiktoken_encoding("cl100k_base")

        cache_key = tokenizer_name

        # Rate limiting: don't try to load the same tokenizer too frequently
        now = time.time()
        if cache_key in self.last_tokenizer_load and now - self.last_tokenizer_load[cache_key] < 5:
            logger.debug(f"Using cached tokenizer for '{tokenizer_name}' (rate limited)")
            return self.transformers_tokenizers.get(cache_key, self.fallback_encoder)

        self.last_tokenizer_load[cache_key] = now

        if cache_key not in self.transformers_tokenizers:
            try:
                logger.info(f"Loading transformers tokenizer: {tokenizer_name}")
                tokenizer = AutoTokenizer.from_pretrained(
                    tokenizer_name,
                    trust_remote_code=False, # Set to False for security
                    low_cpu_mem_usage=True
                )
                self.transformers_tokenizers[cache_key] = tokenizer
                logger.info(f"Successfully loaded tokenizer: {tokenizer_name}")
                return tokenizer

            except Exception as e:
                logger.error(f"Failed to load tokenizer '{tokenizer_name}': {str(e)}")

                # Try fallback tokenizers based on model family
                model_family = next((k for k in self.MODEL_FAMILY_MAPPING if k in model_name.lower()), None)

                if model_family == "llama":
                    fallback_tokenizers = [
                        "hf-internal-testing/llama-tokenizer",
                        "NousResearch/Llama-2-7b-chat-hf",
                        "meta-llama/Llama-3-8b"
                    ]
                elif model_family == "deepseek":
                    fallback_tokenizers = [
                        "meta-llama/Llama-2-7b-hf",  # DeepSeek often uses similar tokenization
                        "deepseek-ai/deepseek-coder-6.7b-base"
                    ]
                elif model_family == "phi":
                    fallback_tokenizers = [
                        "microsoft/phi-1_5",
                        "microsoft/phi-2"
                    ]
                else:
                    fallback_tokenizers = ["gpt2"]  # Universal fallback

                for fallback in fallback_tokenizers:
                    try:
                        logger.info(f"Trying fallback tokenizer: {fallback}")
                        tokenizer = AutoTokenizer.from_pretrained(fallback, trust_remote_code=False)
                        self.transformers_tokenizers[cache_key] = tokenizer
                        logger.info(f"Successfully loaded fallback tokenizer: {fallback}")
                        return tokenizer
                    except Exception as fallback_e:
                        logger.warning(f"Failed fallback tokenizer '{fallback}': {str(fallback_e)}")

                # Ultimate fallback to tiktoken
                logger.warning(f"All tokenizer attempts failed for '{model_name}'. Using cl100k_base.")
                return self._get_tiktoken_encoding("cl100k_base")

        return self.transformers_tokenizers[cache_key]

    def _get_safe_fallback_encoder(self):
        """Get a safe fallback encoder that will always work."""
        try:
            return tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            logger.error(f"Failed to get fallback encoding: {str(e)}")
            try:
                return tiktoken.get_encoding("gpt2")
            except Exception as e2:
                logger.critical(f"Critical failure: could not get any encoding: {str(e2)}")
                # Create a very basic fallback encoder
                class BasicFallbackEncoder:
                    def encode(self, text):
                        # Very rough estimate: 4 characters per token
                        return [text[i:i+4] for i in range(0, len(text), 4)]
                return BasicFallbackEncoder()

    def _fallback_token_count(self, text: str) -> int:
        """
        Ultimate fallback token count estimation.
        Very rough heuristic: 4 characters per token on average.
        """
        if not text:
            return 0
        # Handle special cases
        if len(text) < 10:
            return 1  # Very short text is likely 1 token

        # Rough estimation: 4 chars per token, but account for whitespace and punctuation
        word_count = len(text.split())
        char_count = len(text)

        # Hybrid approach: combine word count and character count
        estimated_tokens = max(1, min(
            word_count * 1.3,  # Words are typically 1-1.3 tokens
            char_count / 3.5   # Average characters per token
        ))

        return int(estimated_tokens)

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
        self.token_estimator = TokenEstimator()

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

    def estimate_tokens(self, text: str, model_name: str = "gpt-4") -> int:
        """Quick token estimation without full encoding"""
        return self.token_estimator.count_tokens(text, model_name)

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
            # Estimate with a general-purpose model first for routing decisions
            context_size = self.estimate_tokens(task["context"])
            task_type = task.get("type", "general")

            # Check if it's a private repo task
            if self._is_ip_task(task.get("context", "")):
                model = "zread" # Force Zread
                reason = "Private repository access required. Using Zread MCP for deep search/reading."

                return {
                    "model": model,
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

            TASK_COUNT.labels(model=model).inc()

            # Re-estimate with the specific model for accuracy
            final_context_size = self.estimate_tokens(task["context"], model_name=model)

            return {
                "model": model,
                "endpoint": self.MODEL_PROFILES[model].model,
                "reason": reason,
                "estimated_cost": final_context_size * self.MODEL_PROFILES[model].cost_per_1k / 1000,
                "context_size": final_context_size
            }

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Route and execute in one call"""
        routing = self.route_task(task)
        task_id = task.get("id", "unknown")

        # Add patent research routing
        if task.get("type") == "patent_research":
            subtype = task.get("subtype", "novelty_check")

            if subtype == "novelty_check":
                async with self.patent as patent_agent:
                    patent_data = await patent_agent.novelty_check(task["context"])
                return await self._synthesize_patent_findings(task, patent_data, routing)

        # Call the appropriate model or agent
        if routing.get("model") == "zread":
            repo_url = task.get("repo_url", "https://github.com/example/repo")
            query = task.get("context", "")
            response = await asyncio.to_thread(self.zread_agent.search_repo, repo_url, query)
        elif "ollama" in routing["endpoint"]:
            response = await self._call_ollama(task, routing)
        else:
            response = await self._call_kimi(task, routing)

        # Handle patent novelty check synthesis
        subtype = task.get("subtype", "")
        if subtype == "novelty_check" and "patent_data" in task:
            return await self._synthesize_patent_findings(task, patent_data, routing)

        return {
            "routing": routing,
            "response": response,
            "timestamp": datetime.now().isoformat()
        }

    async def _synthesize_patent_findings(self, task: Dict[str, Any], patent_data: Dict[str, Any], routing: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize patent findings with normalized schema"""
        findings = patent_data.get("findings", {})
        normalized = findings.get("normalized", {})
        patents = normalized.get("patents", [])
        counts = normalized.get("counts", {})

        # Limit patents to fit context window (25 is safe for most models)
        limited_patents = patents[:25]

        synthesis_prompt = f"""
Based on this patent landscape analysis:
{json.dumps({'counts': counts, 'patents': limited_patents}, indent=2)}

Provide a professional novelty assessment. Include:
1. Novelty score (1-10)
2. Key differentiators vs. existing patents
3. Recommended claim strategy
4. Risks and opportunities
5. Most relevant prior art references
"""

        synthesis_task = {
            "context": synthesis_prompt,
            "model": routing["model"],
            "subtype": "patent_synthesis"
        }

        return await self.execute_task(synthesis_task)


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

    async def _call_kimi(self, task: Dict[str, Any], routing: Dict[str, Any]) -> Dict[str, Any]:
        """Call Kimi-Linear via OpenAI-compatible API"""
        response = requests.post(
            routing["endpoint"],
            headers={"Authorization": "Bearer EMPTY"},
            json={
                "model": "moonshotai/Kimi-Linear-48B-A3B-Instruct",
                "messages": [{"role": "user", "content": task["context"]}],
                "max_tokens": 4096,  # Kimi supports larger context
                "temperature": 0.3,   # Lower temperature for patent analysis
                "top_p": 0.9
            }
        )
        return response.json()

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
