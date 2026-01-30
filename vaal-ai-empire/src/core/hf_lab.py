import logging
import os
from functools import lru_cache

from huggingface_hub import InferenceClient
from sentence_transformers import SentenceTransformer

logger = logging.getLogger("HFLab")

SEO_MODEL_NAME = "all-MiniLM-L6-v2"


# ⚡ Bolt Optimization: Cache the model loading
@lru_cache(maxsize=None)
def get_seo_model():
    """Loads and caches the SentenceTransformer model."""
    try:
        model = SentenceTransformer(SEO_MODEL_NAME)
        logger.info("✅ HF Lab: Local SEO Model Loaded.")
        return model
    except Exception as e:
        logger.warning(f"⚠️ HF Lab: Local SEO Model missing: {e}")
        return None


class HuggingFaceLab:
    """
    The Cost-Optimization Engine.
    Handles low-complexity tasks (Sentiment, SEO, Summaries) for free.
    """

    def __init__(self):
        self.hf_token = os.getenv("HUGGINGFACE_API_KEY")
        self.client = InferenceClient(token=self.hf_token) if self.hf_token else None

        # Load Local SEO Model (CPU-friendly)
        # ⚡ Bolt Optimization: Use the cached model loader
        self.seo_model = get_seo_model()

    def analyze_sentiment(self, text: str):
        """Free Tier Sentiment Analysis"""
        if not self.client:
            return "N/A"
        try:
            model = "cardiffnlp/twitter-roberta-base-sentiment-latest"
            response = self.client.text_classification(text, model=model)
            top = max(response, key=lambda x: x.score)
            return top.label
        except Exception as e:
            logger.error(f"HF Sentiment Error: {e}")
            return "Error"

    def optimize_keywords(self, keywords: list):
        """Free Tier Semantic Analysis (Local)"""
        if not self.seo_model:
            return 0
        embeddings = self.seo_model.encode(keywords)
        return len(embeddings)


class CostRouter:
    """
    The Gatekeeper.
    Decides: Send to 'Intern' (HF) or 'Titan' (Kimi/Mistral)?
    """

    def __init__(self, hf_lab):
        self.lab = hf_lab

    def route_task(self, task_type, complexity):
        if complexity == "low" and self.lab.client:
            return "HUGGING_FACE_FREE"
        else:
            return "TITAN_PREMIUM"
