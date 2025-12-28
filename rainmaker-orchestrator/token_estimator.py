import tiktoken
from typing import Dict, Any, Optional, Union
import logging
from functools import lru_cache

# Set up logging for token estimation issues
logger = logging.getLogger(__name__)

class TokenEstimator:
    """
    Robust token estimator with fallbacks for multiple model families.
    Handles OpenAI models (tiktoken) and open-source models (transformers).
    """

    # Model family mappings to encoding names
    MODEL_FAMILY_MAPPING = {
        # OpenAI GPT-4 family
        "gpt-4": "cl100k_base",
        "gpt-4o": "cl100k_base",
        "gpt-4-turbo": "cl100k_base",
        "gpt-3.5-turbo": "cl100k_base",

        # OpenAI GPT-3 family
        "text-davinci-003": "p50k_base",
        "text-davinci-002": "p50k_base",
        "text-curie-001": "r50k_base",
        "text-babbage-001": "r50k_base",
        "text-ada-001": "r50k_base",

        # Llama family (Meta)
        "llama": "llama",
        "llama2": "llama",
        "llama3": "llama",
        "llama-7b": "llama",
        "llama-13b": "llama",
        "llama-70b": "llama",
        "llama2-7b": "llama",
        "llama2-13b": "llama",
        "llama2-70b": "llama",
        "llama3-8b": "llama",
        "llama3-70b": "llama",
        "phi4-mini": "llama",

        # DeepSeek family
        "deepseek": "deepseek",
        "deepseek-r1": "deepseek",
        "deepseek-coder": "deepseek",

        # Mistral family
        "mistral": "mistral",
        "mixtral": "mistral",

        # Kimi/Moonshot family
        "kimi": "kimi",
        "moonshot": "kimi",

        # Ollama generic models
        "ollama": "cl100k_base",  # Default to OpenAI's tokenizer as reasonable fallback
    }

    def __init__(self):
        self._tiktoken_encodings = {}
        self._transformers_tokenizers = {}
        self._fallback_encoding = self._get_safe_fallback_encoding()

    @lru_cache(maxsize=32)
    def get_encoding_for_model(self, model_name: str) -> Any:
        """
        Get appropriate encoding/tokenizer for a model with fallbacks.
        Uses LRU cache to avoid repeated initialization.
        """
        model_name_lower = model_name.lower()

        try:
            # Try to find model family match
            for family_name, encoding_type in self.MODEL_FAMILY_MAPPING.items():
                if family_name in model_name_lower:
                    if encoding_type == "cl100k_base":
                        return self._get_tiktoken_encoding("cl100k_base")
                    elif encoding_type == "p50k_base":
                        return self._get_tiktoken_encoding("p50k_base")
                    elif encoding_type == "r50k_base":
                        return self._get_tiktoken_encoding("r50k_base")
                    else:
                        return self._get_transformers_tokenizer(encoding_type, model_name)

            # Try OpenAI-specific model detection
            try:
                return tiktoken.encoding_for_model(model_name)
            except KeyError:
                pass

            # Fallback to model name prefix matching
            if model_name_lower.startswith(("gpt-4", "gpt-3.5")):
                return self._get_tiktoken_encoding("cl100k_base")
            elif model_name_lower.startswith("text-davinci"):
                return self._get_tiktoken_encoding("p50k_base")
            elif model_name_lower.startswith(("llama", "llama2", "llama3")):
                return self._get_transformers_tokenizer("llama", model_name)
            elif "deepseek" in model_name_lower:
                return self._get_transformers_tokenizer("deepseek", model_name)
            elif "mistral" in model_name_lower or "mixtral" in model_name_lower:
                return self._get_transformers_tokenizer("mistral", model_name)
            elif "kimi" in model_name_lower or "moonshot" in model_name_lower:
                return self._get_transformers_tokenizer("kimi", model_name)

        except Exception as e:
            logger.warning(f"Error getting encoding for model '{model_name}': {str(e)}")

        # Ultimate fallback
        logger.warning(f"Using fallback encoding for model '{model_name}'")
        return self._fallback_encoding

    def count_tokens(self, text: str, model_name: str) -> int:
        """
        Count tokens in text for a specific model.
        """
        encoding = self.get_encoding_for_model(model_name)

        try:
            if hasattr(encoding, "encode"):
                # tiktoken-style encoding
                return len(encoding.encode(text))
            elif hasattr(encoding, "tokenize") or hasattr(encoding, "__call__"):
                # transformers-style tokenizer
                if hasattr(encoding, "tokenize"):
                    tokens = encoding.tokenize(text)
                else:
                    # Some tokenizers use __call__ directly
                    tokens = encoding(text)["input_ids"]
                return len(tokens)
            else:
                logger.warning(f"Unknown encoding type for model '{model_name}', using fallback")
                return len(self._fallback_encoding.encode(text))
        except Exception as e:
            logger.error(f"Error counting tokens for model '{model_name}': {str(e)}")
            return len(self._fallback_encoding.encode(text))

    def _get_tiktoken_encoding(self, encoding_name: str) -> Any:
        """Get or create a tiktoken encoding with caching."""
        if encoding_name not in self._tiktoken_encodings:
            try:
                self._tiktoken_encodings[encoding_name] = tiktoken.get_encoding(encoding_name)
            except Exception as e:
                logger.error(f"Failed to get tiktoken encoding '{encoding_name}': {str(e)}")
                return self._fallback_encoding
        return self._tiktoken_encodings[encoding_name]

    def _get_transformers_tokenizer(self, model_family: str, full_model_name: str) -> Any:
        """Get or create a transformers tokenizer with caching."""
        # Map model family to specific tokenizer names
        tokenizer_name_map = {
            "llama": "meta-llama/Llama-2-7b-hf",  # Default to Llama-2, works for Llama-3 too
            "deepseek": "deepseek-ai/deepseek-coder-1.3b-base",  # DeepSeek has multiple variants
            "mistral": "mistralai/Mistral-7B-v0.1",
            "kimi": "THUDM/chatglm3-6b",  # Kimi is based on GLM architecture
        }

        tokenizer_name = tokenizer_name_map.get(model_family, "meta-llama/Llama-2-7b-hf")

        if tokenizer_name not in self._transformers_tokenizers:
            try:
                from transformers import AutoTokenizer

                try:
                    # Try to load the specific tokenizer
                    tokenizer = AutoTokenizer.from_pretrained(tokenizer_name, trust_remote_code=True)
                except Exception as e1:
                    logger.warning(f"Failed to load tokenizer '{tokenizer_name}': {str(e1)}")

                    # Fallback to generic tokenizers based on model family
                    if model_family == "llama":
                        # Try alternative Llama tokenizers
                        fallback_names = [
                            "hf-internal-testing/llama-tokenizer",
                            "NousResearch/Llama-2-7b-chat-hf",
                            "meta-llama/Llama-3-8b"
                        ]
                        for fallback_name in fallback_names:
                            try:
                                tokenizer = AutoTokenizer.from_pretrained(fallback_name)
                                logger.info(f"Successfully loaded fallback tokenizer '{fallback_name}'")
                                break
                            except Exception as e2:
                                logger.warning(f"Failed fallback tokenizer '{fallback_name}': {str(e2)}")
                                tokenizer = None

                        if tokenizer is None:
                            logger.error("All Llama tokenizer fallbacks failed, using tiktoken cl100k_base")
                            return self._get_tiktoken_encoding("cl100k_base")

                    elif model_family == "deepseek":
                        # DeepSeek models often use similar tokenization to Llama
                        try:
                            tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-2-7b-hf")
                            logger.info("Using Llama tokenizer as fallback for DeepSeek")
                        except Exception as e2:
                            logger.error(f"DeepSeek tokenizer fallback failed: {str(e2)}")
                            return self._get_tiktoken_encoding("cl100k_base")

                    else:
                        # For other model families, fall back to cl100k_base
                        logger.warning(f"No specific fallback for {model_family}, using cl100k_base")
                        return self._get_tiktoken_encoding("cl100k_base")

                self._transformers_tokenizers[tokenizer_name] = tokenizer

            except ImportError:
                logger.warning("Transformers library not available, falling back to tiktoken")
                return self._get_tiktoken_encoding("cl100k_base")
            except Exception as e:
                logger.error(f"Failed to get transformers tokenizer for {model_family}: {str(e)}")
                return self._get_tiktoken_encoding("cl100k_base")

        return self._transformers_tokenizers[tokenizer_name]

    def _get_safe_fallback_encoding(self) -> Any:
        """Get a safe fallback encoding that will always work."""
        try:
            return tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            logger.error(f"Failed to get fallback encoding: {str(e)}")
            try:
                return tiktoken.get_encoding("gpt2")
            except Exception as e2:
                logger.critical(f"Critical failure: could not get any encoding: {str(e2)}")
                # Create a very basic fallback that just splits on whitespace
                class BasicFallbackEncoder:
                    def encode(self, text):
                        return text.split()
                return BasicFallbackEncoder()
