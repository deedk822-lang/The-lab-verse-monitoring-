"""
Local Image Generation - No API keys required
Uses Stable Diffusion WebUI running locally
"""
import os
import requests
import base64
from typing import Dict, List
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class LocalImageGenerator:
    """Local Stable Diffusion image generation"""

    def __init__(self, host: str = None):
        """
        Initialize local image generator

        Args:
            host: Stable Diffusion WebUI host (default: localhost:7861)
        """
        self.host = host or os.getenv("SD_HOST", "http://localhost:7861")
        self.output_dir = Path("data/generated_images")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Check if SD is running
        self.is_available = self._check_availability()

        if self.is_available:
            logger.info(f"✅ Stable Diffusion available at {self.host}")
        else:
            logger.warning(f"⚠️  Stable Diffusion not available at {self.host}")

    def _check_availability(self) -> bool:
        """Check if Stable Diffusion is running"""
        try:
            response = requests.get(f"{self.host}/sdapi/v1/sd-models", timeout=2)
            return response.status_code == 200
        except:
            return False

    def generate(self, prompt: str, style: str = "professional",
                 width: int = 512, height: int = 512) -> Dict:
        """
        Generate image from text prompt

        Args:
            prompt: Text description of image
            style: Image style preset
            width: Image width (512, 768, 1024)
            height: Image height (512, 768, 1024)
        """
        if not self.is_available:
            return {
                "image_path": self._create_placeholder(prompt),
                "provider": "placeholder",
                "cost_usd": 0.0,
                "error": "Stable Diffusion not available"
            }

        # Enhance prompt with style
        enhanced_prompt = self._enhance_prompt(prompt, style)

        try:
            response = requests.post(
                f"{self.host}/sdapi/v1/txt2img",
                json={
                    "prompt": enhanced_prompt,
                    "negative_prompt": "low quality, blurry, distorted, watermark",
                    "steps": 20,
                    "width": width,
                    "height": height,
                    "cfg_scale": 7,
                    "sampler_name": "DPM++ 2M Karras"
                },
                timeout=120
            )

            if response.status_code != 200:
                raise Exception(f"SD error: {response.text}")

            data = response.json()
            image_data = base64.b64decode(data["images"][0])

            # Save image
            filename = f"sd_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = self.output_dir / filename

            with open(filepath, 'wb') as f:
                f.write(image_data)

            logger.info(f"✅ Generated image: {filename}")

            return {
                "image_path": str(filepath),
                "image_url": str(filepath),
                "provider": "stable-diffusion-local",
                "cost_usd": 0.0,  # Free!
                "prompt": enhanced_prompt
            }

        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            return {
                "image_path": self._create_placeholder(prompt),
                "provider": "placeholder",
                "cost_usd": 0.0,
                "error": str(e)
            }

    def _enhance_prompt(self, prompt: str, style: str) -> str:
        """Enhance prompt with style modifiers"""
        style_modifiers = {
            "professional": "professional photography, high quality, business style, clean, modern, detailed",
            "creative": "creative, vibrant, eye-catching, dynamic composition, colorful, artistic",
            "realistic": "photorealistic, detailed, natural lighting, realistic, high resolution, 4k",
            "artistic": "artistic, stylized, aesthetic, beautiful composition, creative design, painterly"
        }

        modifier = style_modifiers.get(style, style_modifiers["professional"])
        return f"{prompt}, {modifier}"

    def _create_placeholder(self, prompt: str) -> str:
        """Create placeholder when SD unavailable"""
        try:
            from PIL import Image, ImageDraw, ImageFont

            img = Image.new('RGB', (800, 600), color='#2563eb')
            draw = ImageDraw.Draw(img)

            text = f"Generated Image:\n{prompt[:100]}"

            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
            except:
                font = ImageFont.load_default()

            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            position = ((800-text_width)/2, (600-text_height)/2)

            draw.text(position, text, fill='white', font=font)

            filename = f"placeholder_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = self.output_dir / filename
            img.save(filepath)

            return str(filepath)
        except Exception as e:
            logger.error(f"Failed to create placeholder: {e}")
            return "placeholder.png"

    def generate_batch(self, prompts: List[str], style: str = "professional") -> List[Dict]:
        """Generate multiple images"""
        results = []

        for i, prompt in enumerate(prompts):
            logger.info(f"Generating image {i+1}/{len(prompts)}: {prompt[:50]}...")
            result = self.generate(prompt, style=style)
            results.append(result)

        return results
