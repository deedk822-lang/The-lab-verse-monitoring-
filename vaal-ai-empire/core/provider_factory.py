from functools import lru_cache
import logging
from typing import Optional, Any
import importlib

# Configure logger for this module
logger = logging.getLogger(__name__)

# --- Lazily Loaded Text Generation Providers ---

@lru_cache(maxsize=1)
def get_cohere_provider() -> Optional[Any]:
    """Lazily load and return a CohereAPI instance."""
    try:
        CohereAPI = importlib.import_module("vaal-ai-empire.api.cohere").CohereAPI
        logger.info("✅ Cohere provider initialized on-demand")
        return CohereAPI()
    except (ImportError, ValueError) as e:
        logger.warning(f"⚠️  Cohere unavailable: {e}")
        return None

@lru_cache(maxsize=1)
def get_groq_provider() -> Optional[Any]:
    """Lazily load and return a GroqAPI instance."""
    try:
        GroqAPI = importlib.import_module("vaal-ai-empire.api.groq_api").GroqAPI
        logger.info("✅ Groq provider initialized on-demand")
        return GroqAPI()
    except (ImportError, ValueError) as e:
        logger.warning(f"⚠️  Groq unavailable: {e}")
        return None

@lru_cache(maxsize=1)
def get_mistral_provider() -> Optional[Any]:
    """Lazily load and return a MistralAPI instance."""
    try:
        MistralAPI = importlib.import_module("vaal-ai-empire.api.mistral").MistralAPI
        logger.info("✅ Mistral provider initialized on-demand")
        return MistralAPI()
    except (ImportError, ValueError) as e:
        logger.warning(f"⚠️  Mistral unavailable: {e}")
        return None

@lru_cache(maxsize=1)
def get_huggingface_provider() -> Optional[Any]:
    """Lazily load and return a HuggingFaceAPI instance."""
    try:
        HuggingFaceAPI = importlib.import_module("vaal-ai-empire.api.huggingface_api").HuggingFaceAPI
        logger.info("✅ HuggingFace provider initialized on-demand")
        return HuggingFaceAPI()
    except (ImportError, ValueError) as e:
        logger.warning(f"⚠️  HuggingFace unavailable: {e}")
        return None

# --- Lazily Loaded Image Generation Provider ---

@lru_cache(maxsize=1)
def get_image_generator() -> Optional[Any]:
    """Lazily load and return a BusinessImageGenerator instance."""
    try:
        BusinessImageGenerator = importlib.import_module("vaal-ai-empire.api.image_generation").BusinessImageGenerator
        logger.info("✅ Image generation provider initialized on-demand")
        return BusinessImageGenerator()
    except Exception as e:
        logger.warning(f"⚠️  Image generation disabled: {e}")
        return None

# Dictionary mapping provider names to their lazy-loading functions
PROVIDER_FUNCTIONS = {
    "cohere": get_cohere_provider,
    "groq": get_groq_provider,
    "mistral": get_mistral_provider,
    "huggingface": get_huggingface_provider,
}
