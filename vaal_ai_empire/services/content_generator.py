from functools import lru_cache
from typing import Dict, List, Optional, Any
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

# Asynchronous, cached provider initialization
@lru_cache(maxsize=1)
def _get_cached_providers_sync() -> tuple:
    """
    Synchronous wrapper to preserve the lru_cache behavior,
    which is not directly compatible with async functions.
    This initializes and caches all API providers.
    """
    # This function's body is intentionally left minimal.
    # It serves as a memoized entry point to the async initializer.
    return asyncio.run(_initialize_providers())

async def _initialize_providers() -> tuple:
    """
    Initialize and cache all content and image generation providers asynchronously.
    """
    # --- Initialize Text Providers ---
    providers = {
        "cohere": None, "groq": None, "mistral": None,
        "huggingface": None, "kimi": None
    }

    # Helper to initialize a provider and log the outcome
    async def init_provider(name, api_class):
        try:
            providers[name] = api_class()
            logger.info(f"✅ {name.capitalize()} provider initialized")
        except (ImportError, ValueError) as e:
            logger.warning(f"⚠️  {name.capitalize()} unavailable: {e}")

    # Dynamically import and initialize providers
    provider_map = {
        "cohere": "vaal_ai_empire.api.cohere.CohereAPI",
        "groq": "api.groq_api.GroqAPI",
        "mistral": "api.mistral.MistralAPI",
        "huggingface": "api.huggingface_api.HuggingFaceAPI",
        "kimi": "api.kimi.KimiAPI"
    }

    for name, path in provider_map.items():
        try:
            module_path, class_name = path.rsplit('.', 1)
            module = __import__(module_path, fromlist=[class_name])
            api_class = getattr(module, class_name)
            await init_provider(name, api_class)
        except (ImportError, AttributeError) as e:
            logger.warning(f"⚠️  Could not import {name.capitalize()} provider at {path}: {e}")


    available = [k for k, v in providers.items() if v]
    if available:
        logger.info(f"Available text providers: {', '.join(available)}")
    else:
        logger.error("❌ No content generation providers available!")

    # --- Initialize Image & Multimodal Providers ---
    image_generator, multimodal_provider = None, None
    try:
        from api.image_generation import BusinessImageGenerator
        image_generator = BusinessImageGenerator()
        logger.info("✅ Image generation provider initialized")
    except Exception as e:
        logger.warning(f"⚠️  Image generation disabled: {e}")

    try:
        from api.aya_vision import AyaVisionAPI
        multimodal_provider = AyaVisionAPI()
        logger.info("✅ Aya Vision multimodal provider initialized")
    except (ImportError, ValueError) as e:
        logger.warning(f"⚠️  Aya Vision multimodal provider unavailable: {e}")

    return providers, image_generator, multimodal_provider


class ContentFactory:
    """Asynchronous content generation with multiple provider support"""

    def __init__(self, db=None):
        self.db = db
        self.providers, self.image_generator, self.multimodal_provider = _get_cached_providers_sync()

    async def generate_multimodal_content(self, messages: List[Dict[str, Any]], max_new_tokens: int = 300) -> Dict:
        if not self.multimodal_provider:
            raise RuntimeError("Aya Vision multimodal provider is not available.")
        # Assuming multimodal provider has an async method
        return await self.multimodal_provider.generate_from_messages(messages, max_new_tokens)

    async def generate_content(self, prompt: str, max_tokens: int = 500) -> Dict:
        return await self._generate_with_fallback(prompt, max_tokens)

    async def _generate_with_fallback(self, prompt: str, max_tokens: int = 500) -> Dict:
        priority = ["groq", "cohere", "mistral", "kimi", "huggingface"]

        for provider_name in priority:
            provider = self.providers.get(provider_name)
            if not provider:
                continue

            try:
                logger.info(f"Trying {provider_name}...")
                # Use await for all provider calls
                if hasattr(provider, 'generate_content'):
                    result = await provider.generate_content(prompt, max_tokens)
                elif hasattr(provider, 'generate'):
                    result = await provider.generate(prompt, max_tokens)
                elif hasattr(provider, 'query_local'):
                    result = await provider.query_local(prompt)
                else:
                    continue

                # Standardize logging and result structure
                usage = result.get("usage", {})
                cost = usage.get("cost_usd", 0.0)
                tokens = usage.get("output_tokens", 0)

                if self.db:
                    self.db.log_api_usage(provider_name, "generate", usage.get("total_tokens", tokens), cost)

                return {"text": result.get("text", ""), "provider": provider_name, "cost_usd": cost, "tokens": tokens}

            except Exception as e:
                logger.warning(f"{provider_name} failed: {e}")
                continue

        raise Exception("All content generation providers failed")

    async def generate_social_pack(self, business_type: str, language: str = "afrikaans",
                                   num_posts: int = 10, num_images: int = 5) -> Dict:
        logger.info(f"Generating social pack for {business_type} ({language})")

        posts_prompt = self._build_posts_prompt(business_type, language, num_posts)
        # Concurrently generate posts and images
        posts_task = self.generate_content(posts_prompt, max_tokens=2000)
        images_task = self.image_generator.generate_for_business(business_type, count=num_images) if self.image_generator else asyncio.resolve(self._create_placeholder_images(num_images))

        posts_result, image_results = await asyncio.gather(posts_task, images_task, return_exceptions=True)

        if isinstance(posts_result, Exception):
            logger.error(f"Content generation failed: {posts_result}")
            raise posts_result

        posts = self._parse_posts(posts_result.get("text", ""), num_posts)
        images = image_results if not isinstance(image_results, Exception) else self._create_placeholder_images(num_images)

        if isinstance(image_results, Exception):
            logger.error(f"Image generation failed: {image_results}")

        total_cost = posts_result.get("cost_usd", 0.0) + sum(img.get("cost_usd", 0.0) for img in images)

        pack = {"posts": posts, "images": images, "metadata": {"business_type": business_type, "language": language, "generated_at": datetime.now().isoformat(), "provider": posts_result.get("provider"), "cost_usd": total_cost, "tokens_used": posts_result.get("tokens", 0)}}

        if self.db:
            self.db.save_content_pack(client_id="system", pack_data=pack, posts_count=len(posts), images_count=len(images), cost_usd=total_cost)

        logger.info(f"✅ Generated {len(posts)} posts and {len(images)} images")
        return pack

    async def generate_email_sequence(self, business_name: str, business_type: str, days: int = 7) -> List[Dict]:
        cohere_provider = self.providers.get("cohere")
        if not cohere_provider:
            logger.error("Cohere provider not available for email generation.")
            return self._create_template_emails(business_name, days)
        # Directly call the optimized async method
        return await cohere_provider.generate_email_sequence(business_type, days)

    async def close_providers(self):
        """Gracefully close all async provider clients."""
        for provider in self.providers.values():
            if hasattr(provider, 'close'):
                await provider.close()
        logger.info("All async providers closed.")

    def _build_posts_prompt(self, business_type: str, language: str, num_posts: int) -> str:
        # This method remains synchronous as it's CPU-bound
        # ... (rest of the synchronous methods remain unchanged)
        language_instructions = {"afrikaans": "Write in Afrikaans (South African dialect)", "english": "Write in English (South African style)", "both": "Write 50% in Afrikaans, 50% in English"}
        lang_instruction = language_instructions.get(language, language_instructions["afrikaans"])
        business_contexts = {"butchery": "a local butchery in Vaal Triangle, South Africa. Focus on fresh meat, quality cuts, special offers, and traditional braai culture.", "auto_repair": "an auto repair shop in Vaal Triangle, South Africa. Focus on reliable service, quality parts, professional mechanics, and vehicle maintenance tips.", "cafe": "a coffee shop in Vaal Triangle, South Africa. Focus on fresh coffee, baked goods, cozy atmosphere, and community gathering.", "restaurant": "a restaurant in Vaal Triangle, South Africa. Focus on delicious food, specials, events, and dining experience.", "salon": "a hair and beauty salon in Vaal Triangle, South Africa. Focus on latest styles, professional service, beauty tips, and special treatments.", "retail": "a retail store in Vaal Triangle, South Africa. Focus on product quality, special offers, customer service, and new arrivals."}
        context = business_contexts.get(business_type, f"a {business_type} business in Vaal Triangle, South Africa")
        prompt = f"""Generate {num_posts} engaging social media posts for {context}

REQUIREMENTS:
- {lang_instruction}
- Each post should be 50-150 words
- Include relevant emojis
- Add clear call-to-action
- Make it engaging and authentic
- Include variety: promotions, tips, behind-the-scenes, customer appreciation
- Format: One post per line, separated by "---"

Example format:
🥩 Freshly cut prime beef ready for your weekend braai! Come see us today for the best quality meat in Vaal. Special: Buy 2kg, get 500g free! #Vaalbraai #FreshMeat
---
💡 Braai Tip: Let your meat rest for 5 minutes after grilling for maximum juiciness. Visit us for expert advice and premium cuts! 🔥
---

Now generate {num_posts} unique posts:"""
        return prompt

    def _parse_posts(self, text: str, expected_count: int) -> List[str]:
        if "---" in text:
            posts = [p.strip() for p in text.split("---") if p.strip()]
        else:
            posts = [p.strip() for p in text.split("\n\n") if p.strip()]

        cleaned_posts = []
        for post in posts:
            post = post.split(".", 1)[-1].strip() if post[0].isdigit() else post
            if post.lower().startswith("post "):
                post = post.split(":", 1)[-1].strip() if ":" in post else post
            if len(post) > 30:
                cleaned_posts.append(post)

        while len(cleaned_posts) < expected_count:
            if cleaned_posts:
                base_post = cleaned_posts[len(cleaned_posts) % len(cleaned_posts)]
                cleaned_posts.append(base_post + " 🌟")
            else:
                cleaned_posts.append("Coming soon! Stay tuned for exciting updates. 🎉")
        return cleaned_posts[:expected_count]

    def _create_placeholder_images(self, count: int) -> List[Dict]:
        return [{"prompt": f"Business image {i+1}", "image_url": f"https://via.placeholder.com/800x600?text=Image+{i+1}", "provider": "placeholder", "cost_usd": 0.0} for i in range(count)]

    def _create_template_emails(self, business_name: str, days: int) -> List[Dict]:
        templates = [{"subject": f"Welcome to {business_name}!", "body": f"Thank you for connecting with {business_name}. We're excited to serve you!"}, {"subject": f"Special Offer from {business_name}", "body": f"Check out our special offers this week at {business_name}!"}, {"subject": f"Tips & Tricks from {business_name}", "body": f"Here are some expert tips from the team at {business_name}."}]
        emails = []
        for i in range(days):
            template = templates[i % len(templates)]
            emails.append({"day": i + 1, "subject": template["subject"], "body": template["body"]})
        return emails

    def get_provider_status(self) -> Dict:
        return {provider: "available" if client else "unavailable" for provider, client in self.providers.items()}
