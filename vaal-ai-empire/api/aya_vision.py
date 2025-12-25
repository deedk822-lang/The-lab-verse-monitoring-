import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

try:
    from transformers import pipeline
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    logger.warning("⚠️  Transformers library not found or not the correct version. AyaVisionAPI will be unavailable.")
    TRANSFORMERS_AVAILABLE = False

class AyaVisionAPI:
    """
    API wrapper for the CohereLabs/aya-vision-32b multimodal model.
    """
    def __init__(self):
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError("Please install the specific version of 'transformers' and 'torch' to use the AyaVisionAPI.")

        self.model_id = "CohereLabs/aya-vision-32b"
        try:
            logger.info(f"🚀 Initializing Aya Vision pipeline for model: {self.model_id}...")
            self.pipe = pipeline(
                model=self.model_id,
                task="image-text-to-text",
                device_map="auto",
                torch_dtype=torch.float16
            )
            logger.info("✅ Aya Vision pipeline initialized successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Aya Vision pipeline: {e}")
            raise ValueError(f"Could not initialize AyaVisionAPI: {e}")

    def generate_from_messages(self, messages: List[Dict[str, Any]], max_new_tokens: int = 300) -> Dict:
        """
        Generates text content based on a list of messages which can include images and text.
        """
        if not self.pipe:
            raise RuntimeError("Aya Vision pipeline is not initialized.")

        try:
            logger.info("Generating content with Aya Vision...")
            outputs = self.pipe(messages, max_new_tokens=max_new_tokens, return_full_text=False)
<<<<<<< HEAD

            generated_text = outputs[0]["generated_text"]

=======

            generated_text = outputs[0]["generated_text"]

>>>>>>> c00699664d3818edf437bf12f56f434451084e1b
            # The pipeline API doesn't expose token usage, so we return placeholders
            return {
                "text": generated_text,
                "usage": {
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "cost_usd": 0.0  # Self-hosted model, no direct API cost
                }
            }
        except Exception as e:
            logger.error(f"❌ Aya Vision content generation failed: {e}")
            raise
