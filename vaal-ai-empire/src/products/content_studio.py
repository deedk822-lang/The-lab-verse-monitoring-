import logging
import os
from datetime import datetime
from pathlib import Path

from huggingface_hub import InferenceClient

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ContentStudio")


class ContentStudio:
    """
    The Content Factory.
    Uses Hugging Face Inference API to generate marketing assets.
    - Text: Meta Llama 3.1 8B
    - Image: FLUX.1-dev
    """

    def __init__(self):
        self.token = os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HF_TOKEN")

        if not self.token:
            logger.error("❌ HUGGINGFACE_API_KEY is missing. Studio cannot operate.")
            self.client = None
        else:
            self.client = InferenceClient(token=self.token)
            logger.info("✅ Content Studio Online (Connected to Hugging Face).")

        # Define Models
        self.text_model = "meta-llama/Meta-Llama-3.1-8B-Instruct"
        self.image_model = "black-forest-labs/FLUX.1-dev"

        # Setup Output Directory
        self.output_dir = Path("content_output")
        self.output_dir.mkdir(exist_ok=True)

    def generate_social_bundle(self, niche: str, topic: str):
        """
        Generates a text caption and a matching visual asset.
        """
        if not self.client:
            return {"status": "error", "message": "API Key Missing"}

        logger.info(f"🎨 Starting Job: {niche} -> {topic}")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # --- STEP 1: TEXT GENERATION (Llama 3.1) ---
        caption = ""
        try:
            logger.info(f"   > Prompting {self.text_model}...")

            prompt = f"""
            <|begin_of_text|><|start_header_id|>system<|end_header_id|>
            You are a professional social media manager. Write a viral LinkedIn post.
            Target Audience: {niche}
            Topic: {topic}
            Style: Professional, engaging, use bullet points and emojis.
            <|eot_id|><|start_header_id|>user<|end_header_id|>
            Write the post now.<|eot_id|><|start_header_id|>assistant<|end_header_id|>
            """

            response = self.client.text_generation(
                prompt, model=self.text_model, max_new_tokens=400, temperature=0.7
            )
            caption = response.strip()
            logger.info("   ✅ Text Generated.")

        except Exception as e:
            logger.error(f"   ❌ Text Generation Failed: {e}")
            caption = f"Error generating text: {str(e)}"

        # --- STEP 2: IMAGE GENERATION (FLUX) ---
        image_path_str = "None"
        try:
            logger.info(f"   > Prompting {self.image_model}...")

            image_prompt = f"Professional photography for {niche}, centered on {topic}, cinematic lighting, 8k resolution, highly detailed, photorealistic, rule of thirds"

            image = self.client.text_to_image(image_prompt, model=self.image_model)

            # Save Image locally
            filename = f"gen_{timestamp}.png"
            file_path = self.output_dir / filename
            image.save(file_path)
            image_path_str = str(file_path)

            logger.info(f"   ✅ Image Saved: {image_path_str}")

        except Exception as e:
            logger.error(f"   ❌ Image Generation Failed: {e}")
            image_path_str = "Error generating image"

        # --- STEP 3: DELIVERABLE ---
        return {
            "status": "success",
            "timestamp": timestamp,
            "caption": caption,
            "local_image_path": image_path_str,
            "models_used": [self.text_model, self.image_model],
        }


if __name__ == "__main__":
    # Local Test
    studio = ContentStudio()
    if studio.client:
        print("--- RUNNING TEST GENERATION ---")
        result = studio.generate_social_bundle(
            "Tech Startups", "The Future of AI Agents in South Africa"
        )
        print("\nCAPTION:")
        print(result["caption"])
        print(f"\nIMAGE: {result['local_image_path']}")
