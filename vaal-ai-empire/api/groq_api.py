import os
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GroqAPI:
    """Groq API wrapper for fast inference"""

    def __init__(self):
        try:
            from groq import Groq
        except ImportError:
            raise ImportError("Groq SDK not installed. Please install it with 'pip install groq'")

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable not set.")

        self.client = Groq(api_key=api_key)

        # Available models
        self.models = {
            "mixtral": "mixtral-8x7b-32768",
            "llama2": "llama2-70b-4096",
            "gemma": "gemma-7b-it",
            "llama3": "llama3-70b-8192"
        }
        self.default_model = self.models["mixtral"]

        # Pricing (per 1M tokens, USD)
        self.pricing = {
            "mixtral-8x7b-32768": {"input": 0.27, "output": 0.27},
            "llama2-70b-4096": {"input": 0.70, "output": 0.80},
            "llama3-70b-8192": {"input": 0.59, "output": 0.79}
        }

        self.usage_log = []

    def generate(self, prompt: str, max_tokens: int = 500,
                model: str = None, temperature: float = 0.7) -> Dict:
        """Generate text with cost tracking"""
        model = model or self.default_model

        try:
            completion = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant specializing in creating engaging social media content."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=1,
                stream=False
            )

            # Extract usage
            usage = {
                "prompt_tokens": completion.usage.prompt_tokens,
                "completion_tokens": completion.usage.completion_tokens,
                "total_tokens": completion.usage.total_tokens
            }

            # Calculate cost
            pricing = self.pricing.get(model, self.pricing[self.default_model])
            cost_usd = (
                (usage["prompt_tokens"] / 1_000_000) * pricing["input"] +
                (usage["completion_tokens"] / 1_000_000) * pricing["output"]
            )

            usage["cost_usd"] = cost_usd
            self.usage_log.append({
                "model": model,
                "usage": usage,
                "timestamp": completion.created
            })

            return {
                "text": completion.choices[0].message.content,
                "model": model,
                "usage": usage,
                "cost_usd": cost_usd,
                "finish_reason": completion.choices[0].finish_reason
            }

        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise e

    def chat(self, messages: List[Dict], model: str = None,
             max_tokens: int = 500, temperature: float = 0.7) -> Dict:
        """Multi-turn chat with cost tracking"""
        model = model or self.default_model

        try:
            completion = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=1
            )

            # Extract usage and calculate cost
            usage = {
                "prompt_tokens": completion.usage.prompt_tokens,
                "completion_tokens": completion.usage.completion_tokens,
                "total_tokens": completion.usage.total_tokens
            }

            pricing = self.pricing.get(model, self.pricing[self.default_model])
            cost_usd = (
                (usage["prompt_tokens"] / 1_000_000) * pricing["input"] +
                (usage["completion_tokens"] / 1_000_000) * pricing["output"]
            )
            usage["cost_usd"] = cost_usd

            return {
                "text": completion.choices[0].message.content,
                "message": completion.choices[0].message,
                "model": model,
                "usage": usage,
                "cost_usd": cost_usd
            }

        except Exception as e:
            logger.error(f"Groq chat error: {e}")
            raise e

    def get_total_cost(self) -> float:
        """Get total cost from usage log"""
        return sum(entry["usage"]["cost_usd"] for entry in self.usage_log)

    def list_models(self) -> List[str]:
        """List available models"""
        try:
            models = self.client.models.list()
            return [model.id for model in models.data]
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return list(self.models.values())