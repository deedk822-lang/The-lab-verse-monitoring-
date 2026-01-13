import os
from typing import Dict, Optional
import logging
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HuggingFaceAPI:
    """HuggingFace Inference API wrapper"""

    def __init__(self):
        self.api_token = os.getenv("HUGGINGFACE_TOKEN")
        if not self.api_token:
            raise ValueError("HUGGINGFACE_TOKEN environment variable not set.")

        self.api_base = "https://api-inference.huggingface.co/models"
        self.headers = {"Authorization": f"Bearer {self.api_token}"}
        self.session = requests.Session()

        # Available models for different tasks
        self.models = {
            "text_generation": {
                "small": "microsoft/phi-2",
                "medium": "mistralai/Mistral-7B-Instruct-v0.2",
                "large": "meta-llama/Llama-2-70b-chat-hf"
            },
            "embeddings": {
                "default": "sentence-transformers/all-MiniLM-L6-v2",
                "multilingual": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
            },
            "summarization": {
                "default": "facebook/bart-large-cnn"
            }
        }

        self.default_model = self.models["text_generation"]["small"]
        self.usage_log = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    def close(self):
        """Close the requests session to release resources."""
        self.session.close()

    def generate(self, prompt: str, max_tokens: int = 500,
                model: str = None, temperature: float = 0.7,
                wait_for_model: bool = True) -> Dict:
        """Generate text using HuggingFace models"""
        model = model or self.default_model
        api_url = f"{self.api_base}/{model}"

        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": temperature,
                "return_full_text": False,
                "do_sample": True
            },
            "options": {
                "wait_for_model": wait_for_model,
                "use_cache": False
            }
        }

        try:
            response = self.session.post(
                api_url,
                headers=self.headers,
                json=payload,
                timeout=60
            )

            if response.status_code == 503:
                # Model is loading
                logger.warning(f"Model {model} is loading. This may take 20-30 seconds...")
                if wait_for_model:
                    # Retry after waiting
                    import time
                    time.sleep(20)
                    return self.generate(prompt, max_tokens, model, temperature, wait_for_model=False)
                else:
                    raise Exception("Model is still loading. Please try again.")

            if response.status_code != 200:
                raise Exception(f"HuggingFace API error ({response.status_code}): {response.text}")

            result = response.json()

            # Handle response format
            if isinstance(result, list) and len(result) > 0:
                text = result[0].get("generated_text", "")
            else:
                text = result.get("generated_text", str(result))

            self.usage_log.append({
                "model": model,
                "prompt_length": len(prompt),
                "response_length": len(text),
                "cost_usd": 0.0  # Free tier
            })

            return {
                "text": text,
                "model": model,
                "cost_usd": 0.0  # Free tier (rate limited)
            }

        except Exception as e:
            logger.error(f"HuggingFace API error: {e}")
            raise e

    def embed(self, texts: list, model: str = None) -> Dict:
        """Generate embeddings for text"""
        model = model or self.models["embeddings"]["default"]
        api_url = f"{self.api_base}/{model}"

        try:
            response = self.session.post(
                api_url,
                headers=self.headers,
                json={
                    "inputs": texts,
                    "options": {"wait_for_model": True}
                },
                timeout=30
            )

            if response.status_code != 200:
                raise Exception(f"Embedding error ({response.status_code}): {response.text}")

            embeddings = response.json()

            return {
                "embeddings": embeddings,
                "model": model,
                "cost_usd": 0.0
            }

        except Exception as e:
            logger.error(f"Embedding error: {e}")
            raise e

    def summarize(self, text: str, max_length: int = 150,
                 min_length: int = 50) -> Dict:
        """Summarize text"""
        model = self.models["summarization"]["default"]
        api_url = f"{self.api_base}/{model}"

        try:
            response = self.session.post(
                api_url,
                headers=self.headers,
                json={
                    "inputs": text,
                    "parameters": {
                        "max_length": max_length,
                        "min_length": min_length
                    },
                    "options": {"wait_for_model": True}
                },
                timeout=60
            )

            if response.status_code != 200:
                raise Exception(f"Summarization error ({response.status_code}): {response.text}")

            result = response.json()

            if isinstance(result, list) and len(result) > 0:
                summary = result[0].get("summary_text", "")
            else:
                summary = result.get("summary_text", "")

            return {
                "summary": summary,
                "model": model,
                "cost_usd": 0.0
            }

        except Exception as e:
            logger.error(f"Summarization error: {e}")
            raise e

    def chat(self, messages: list, model: str = None,
            max_tokens: int = 500) -> Dict:
        """Chat interface for instruction-following models"""

        # Format messages into a single prompt
        prompt = self._format_chat_prompt(messages)

        return self.generate(prompt, max_tokens=max_tokens, model=model)

    def _format_chat_prompt(self, messages: list) -> str:
        """Format chat messages into a prompt"""
        prompt_parts = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")

        prompt_parts.append("Assistant:")
        return "\n".join(prompt_parts)

    def check_model_status(self, model: str) -> Dict:
        """Check if a model is loaded and ready"""
        api_url = f"{self.api_base}/{model}"

        try:
            response = requests.post(
                api_url,
                headers=self.headers,
                json={"inputs": "test"},
                timeout=5
            )

            return {
                "model": model,
                "status": "ready" if response.status_code == 200 else "loading",
                "status_code": response.status_code
            }

        except Exception as e:
            return {
                "model": model,
                "status": "error",
                "error": str(e)
            }


class LocalHuggingFace:
    """Local HuggingFace model inference (no API calls)"""

    def __init__(self, model_name: str = "microsoft/phi-2",
                 cache_dir: Optional[str] = None):
        """
        Initialize local model

        Args:
            model_name: HuggingFace model identifier
            cache_dir: Directory to cache models
        """
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            import torch
        except ImportError:
            raise ImportError("transformers and torch not installed. Install with: pip install transformers torch")

        self.model_name = model_name
        self.cache_dir = cache_dir

        logger.info(f"Loading model {model_name}...")

        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            cache_dir=cache_dir
        )

        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            cache_dir=cache_dir,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None,
            low_cpu_mem_usage=True
        )

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Model loaded on {self.device}")

    def generate(self, prompt: str, max_tokens: int = 500,
                temperature: float = 0.7) -> Dict:
        """Generate text locally"""
        import torch

        # Tokenize
        inputs = self.tokenizer(prompt, return_tensors="pt")

        if self.device == "cuda":
            inputs = {k: v.cuda() for k, v in inputs.items()}

        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=True,
                top_p=0.9,
                pad_token_id=self.tokenizer.eos_token_id
            )

        # Decode
        text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Remove input prompt from output
        if text.startswith(prompt):
            text = text[len(prompt):].strip()

        return {
            "text": text,
            "model": self.model_name,
            "cost_usd": 0.0,
            "device": self.device
        }