"""
Real Image Generation Service
Supports multiple providers: Stable Diffusion, DALL-E, Replicate
"""

import os
import logging
import base64
from typing import Dict, List, Optional
from .shared_session import http
from datetime import datetime
from pathlib import Path
import io

logger = logging.getLogger(__name__)

class ImageGenerator:
    """Multi-provider image generation service"""

    def __init__(self):
        self.providers = self._detect_available_providers()
        self.output_dir = Path("data/generated_images")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Cost tracking (per image, USD)
        self.costs = {
            "stability": 0.02,      # Stable Diffusion API
            "replicate": 0.005,     # Replicate SDXL
            "huggingface": 0.0,     # Free inference (rate limited)
            "local": 0.0            # Local Stable Diffusion
        }

    def _detect_available_providers(self) -> Dict[str, bool]:
        """Detect which image generation providers are available"""
        providers = {
            "stability": bool(os.getenv("STABILITY_API_KEY")),
            "replicate": bool(os.getenv("REPLICATE_API_TOKEN")),
            "huggingface": bool(os.getenv("HUGGINGFACE_TOKEN")),
            "local": self._check_local_sd()
        }

        available = [p for p, status in providers.items() if status]
        if available:
            logger.info(f"Available image providers: {', '.join(available)}")
        else:
            logger.warning("No image generation providers configured")

        return providers

    def _check_local_sd(self) -> bool:
        """Check if local Stable Diffusion is available"""
        try:
            # Check for common SD endpoints
            endpoints = [
                "http://localhost:7860",  # Automatic1111
                "http://localhost:5000",  # Custom SD server
            ]

            for endpoint in endpoints:
                try:
                    response = http.get(f"{endpoint}/sdapi/v1/sd-models", timeout=2)
                    if response.status_code == 200:
                        logger.info(f"Local SD found at {endpoint}")
                        return True
                except:
                    continue

            return False
        except Exception:
            return False

    def generate(self, prompt: str, style: str = "professional",
                 provider: str = "auto") -> Dict:
        """
        Generate image from text prompt

        Args:
            prompt: Text description of image
            style: Image style (professional, creative, realistic, artistic)
            provider: Provider to use (auto, stability, replicate, huggingface, local)

        Returns:
            Dict with image_url, provider, cost_usd
        """
        # Enhance prompt with style
        enhanced_prompt = self._enhance_prompt(prompt, style)

        # Select provider
        if provider == "auto":
            provider = self._select_best_provider()

        try:
            if provider == "stability" and self.providers["stability"]:
                return self._generate_stability(enhanced_prompt)
            elif provider == "replicate" and self.providers["replicate"]:
                return self._generate_replicate(enhanced_prompt)
            elif provider == "huggingface" and self.providers["huggingface"]:
                return self._generate_huggingface(enhanced_prompt)
            elif provider == "local" and self.providers["local"]:
                return self._generate_local(enhanced_prompt)
            else:
                # Fallback to any available provider
                return self._generate_fallback(enhanced_prompt)

        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            return {
                "image_url": self._create_placeholder(prompt),
                "provider": "placeholder",
                "cost_usd": 0.0,
                "error": str(e)
            }

    def _enhance_prompt(self, prompt: str, style: str) -> str:
        """Enhance prompt with style modifiers"""
        style_modifiers = {
            "professional": "professional photography, high quality, business style, clean, modern",
            "creative": "creative, vibrant, eye-catching, dynamic composition, colorful",
            "realistic": "photorealistic, detailed, natural lighting, realistic, high resolution",
            "artistic": "artistic, stylized, aesthetic, beautiful composition, creative design"
        }

        modifier = style_modifiers.get(style, style_modifiers["professional"])
        return f"{prompt}, {modifier}"

    def _select_best_provider(self) -> str:
        """Select best available provider"""
        priority = ["replicate", "huggingface", "stability", "local"]

        for provider in priority:
            if self.providers[provider]:
                return provider

        return "placeholder"

    def _generate_stability(self, prompt: str) -> Dict:
        """Generate using Stability AI API"""
        api_key = os.getenv("STABILITY_API_KEY")

        response = http.post(
            "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "text_prompts": [{"text": prompt}],
                "cfg_scale": 7,
                "height": 1024,
                "width": 1024,
                "samples": 1,
                "steps": 30,
            },
            timeout=60
        )

        if response.status_code != 200:
            raise Exception(f"Stability AI error: {response.text}")

        data = response.json()
        image_data = base64.b64decode(data["artifacts"][0]["base64"])

        # Save image
        filename = f"stability_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = self.output_dir / filename

        with open(filepath, 'wb') as f:
            f.write(image_data)

        return {
            "image_url": str(filepath),
            "image_path": str(filepath),
            "provider": "stability",
            "cost_usd": self.costs["stability"],
            "prompt": prompt
        }

    def _generate_replicate(self, prompt: str) -> Dict:
        """Generate using Replicate API"""
        api_token = os.getenv("REPLICATE_API_TOKEN")

        import replicate

        output = replicate.run(
            "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
            input={
                "prompt": prompt,
                "num_outputs": 1,
                "guidance_scale": 7.5,
                "num_inference_steps": 30
            }
        )

        # Download image
        image_url = output[0]
        image_data = http.get(image_url).content

        # Save image
        filename = f"replicate_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = self.output_dir / filename

        with open(filepath, 'wb') as f:
            f.write(image_data)

        return {
            "image_url": str(filepath),
            "image_path": str(filepath),
            "provider": "replicate",
            "cost_usd": self.costs["replicate"],
            "prompt": prompt
        }

    def _generate_huggingface(self, prompt: str) -> Dict:
        """Generate using HuggingFace Inference API"""
        api_token = os.getenv("HUGGINGFACE_TOKEN")

        # Use Stable Diffusion XL on HuggingFace
        API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"

        headers = {"Authorization": f"Bearer {api_token}"}

        response = http.post(
            API_URL,
            headers=headers,
            json={"inputs": prompt},
            timeout=60
        )

        if response.status_code != 200:
            raise Exception(f"HuggingFace error: {response.text}")

        # Save image
        filename = f"hf_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = self.output_dir / filename

        with open(filepath, 'wb') as f:
            f.write(response.content)

        return {
            "image_url": str(filepath),
            "image_path": str(filepath),
            "provider": "huggingface",
            "cost_usd": self.costs["huggingface"],
            "prompt": prompt
        }

    def _generate_local(self, prompt: str) -> Dict:
        """Generate using local Stable Diffusion"""
        # Automatic1111 API
        endpoint = "http://localhost:7860"

        response = http.post(
            f"{endpoint}/sdapi/v1/txt2img",
            json={
                "prompt": prompt,
                "steps": 20,
                "width": 512,
                "height": 512,
                "cfg_scale": 7
            },
            timeout=120
        )

        if response.status_code != 200:
            raise Exception(f"Local SD error: {response.text}")

        data = response.json()
        image_data = base64.b64decode(data["images"][0])

        # Save image
        filename = f"local_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = self.output_dir / filename

        with open(filepath, 'wb') as f:
            f.write(image_data)

        return {
            "image_url": str(filepath),
            "image_path": str(filepath),
            "provider": "local",
            "cost_usd": self.costs["local"],
            "prompt": prompt
        }

    def _generate_fallback(self, prompt: str) -> Dict:
        """Fallback: try all available providers"""
        for provider in ["replicate", "huggingface", "stability", "local"]:
            if self.providers[provider]:
                try:
                    logger.info(f"Trying fallback provider: {provider}")
                    return self.generate(prompt, provider=provider)
                except Exception as e:
                    logger.warning(f"Provider {provider} failed: {e}")
                    continue

        # Last resort: placeholder
        return {
            "image_url": self._create_placeholder(prompt),
            "provider": "placeholder",
            "cost_usd": 0.0
        }

    def _create_placeholder(self, prompt: str) -> str:
        """Create placeholder image with text"""
        try:
            from PIL import Image, ImageDraw, ImageFont

            # Create image
            img = Image.new('RGB', (800, 600), color='#2563eb')
            draw = ImageDraw.Draw(img)

            # Add text
            text = f"Generated Image:\n{prompt[:100]}"

            # Try to use a font, fallback to default
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
            except:
                font = ImageFont.load_default()

            # Center text
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            position = ((800-text_width)/2, (600-text_height)/2)

            draw.text(position, text, fill='white', font=font)

            # Save
            filename = f"placeholder_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = self.output_dir / filename
            img.save(filepath)

            return str(filepath)

        except Exception as e:
            logger.error(f"Failed to create placeholder: {e}")
            return "https://via.placeholder.com/800x600?text=Image+Generation+Unavailable"

    def generate_batch(self, prompts: List[str], style: str = "professional") -> List[Dict]:
        """Generate multiple images"""
        results = []

        for i, prompt in enumerate(prompts):
            logger.info(f"Generating image {i+1}/{len(prompts)}: {prompt[:50]}...")

            try:
                result = self.generate(prompt, style=style)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to generate image {i+1}: {e}")
                results.append({
                    "image_url": self._create_placeholder(prompt),
                    "provider": "error",
                    "cost_usd": 0.0,
                    "error": str(e)
                })

        return results

    def get_status(self) -> Dict:
        """Get service status"""
        return {
            "available_providers": [p for p, status in self.providers.items() if status],
            "total_providers": len([p for p in self.providers.values() if p]),
            "output_dir": str(self.output_dir),
            "costs": self.costs
        }


class BusinessImageGenerator:
    """Specialized image generator for business content"""

    def __init__(self):
        self.generator = ImageGenerator()

        # Business-specific prompts
        self.templates = {
            "butchery": [
                "Fresh quality meat cuts on display in professional butchery",
                "Butcher preparing premium meat products, South African style",
                "Clean modern butchery counter with variety of meats",
            ],
            "auto_repair": [
                "Professional mechanic working in modern auto repair shop",
                "Clean organized auto repair garage with tools",
                "Car on lift being serviced by professional technician",
            ],
            "cafe": [
                "Cozy coffee shop interior with customers enjoying coffee",
                "Barista making latte art in professional coffee machine",
                "Fresh pastries and coffee display in modern cafe",
            ],
            "restaurant": [
                "Delicious food plating in restaurant setting",
                "Modern restaurant interior with happy customers",
                "Chef preparing food in professional kitchen",
            ],
            "salon": [
                "Modern hair salon interior with stylists working",
                "Professional hairdresser styling client hair",
                "Clean contemporary salon with comfortable seating",
            ],
            "retail": [
                "Modern retail store with organized product displays",
                "Shopping interior with customers browsing products",
                "Clean retail space with good lighting and displays",
            ]
        }

    def generate_for_business(self, business_type: str, count: int = 5) -> List[Dict]:
        """Generate business-specific images"""
        prompts = self.templates.get(business_type, self.templates["retail"])

        # Cycle through templates if we need more images
        selected_prompts = []
        for i in range(count):
            selected_prompts.append(prompts[i % len(prompts)])

        logger.info(f"Generating {count} images for {business_type}")
        return self.generator.generate_batch(selected_prompts, style="professional")