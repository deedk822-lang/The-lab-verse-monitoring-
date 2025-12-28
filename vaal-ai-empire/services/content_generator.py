from functools import lru_cache
from typing import Dict, List, Optional, Tuple, Any
import logging
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


# ⚡ Bolt Optimization: Cache provider initialization
# This function is decorated with lru_cache to ensure that the expensive
# process of initializing all API providers only happens once.
@lru_cache(maxsize=1)
def _get_cached_providers() -> Tuple[Dict[str, Any], Optional[Any]]:
    """
    Initialize and cache all content and image generation providers.
    This function is executed only once, and its result is cached.
    """
    # --- Initialize Text Providers ---
    providers = {
        "cohere": None,
        "groq": None,
        "mistral": None,
        "huggingface": None,
        "kimi": None
    }

    # Try Cohere
    try:
        from api.cohere import CohereAPI
        providers["cohere"] = CohereAPI()
        logger.info("✅ Cohere provider initialized")
    except (ImportError, ValueError) as e:
        logger.warning(f"⚠️  Cohere unavailable: {e}")

    # Try Groq
    try:
        from api.groq_api import GroqAPI
        providers["groq"] = GroqAPI()
        logger.info("✅ Groq provider initialized")
    except (ImportError, ValueError) as e:
        logger.warning(f"⚠️  Groq unavailable: {e}")

    # Try Mistral (local via Ollama)
    try:
        from api.mistral import MistralAPI
        providers["mistral"] = MistralAPI()
        logger.info("✅ Mistral provider initialized")
    except (ImportError, ValueError) as e:
        logger.warning(f"⚠️  Mistral unavailable: {e}")

    # Try HuggingFace
    try:
        from api.huggingface_api import HuggingFaceAPI
        providers["huggingface"] = HuggingFaceAPI()
        logger.info("✅ HuggingFace provider initialized")
    except (ImportError, ValueError) as e:
        logger.warning(f"⚠️  HuggingFace unavailable: {e}")

    # Try Kimi
    try:
        from api.kimi import KimiAPI
        providers["kimi"] = KimiAPI()
        logger.info("✅ Kimi provider initialized")
    except (ImportError, ValueError) as e:
        logger.warning(f"⚠️  Kimi unavailable: {e}")

    available = [k for k, v in providers.items() if v is not None]
    if available:
        logger.info(f"Available text providers: {', '.join(available)}")
    else:
        logger.error("❌ No content generation providers available!")

    # --- Initialize Image Generator ---
    image_generator = None
    try:
        from api.image_generation import BusinessImageGenerator
        image_generator = BusinessImageGenerator()
        logger.info("✅ Image generation provider initialized")
    except Exception as e:
        logger.warning(f"⚠️  Image generation disabled: {e}")

    # --- Initialize Multimodal Provider ---
    multimodal_provider = None
    try:
        from api.aya_vision import AyaVisionAPI
        multimodal_provider = AyaVisionAPI()
        logger.info("✅ Aya Vision multimodal provider initialized")
    except (ImportError, ValueError) as e:
        logger.warning(f"⚠️  Aya Vision multimodal provider unavailable: {e}")

    return providers, image_generator, multimodal_provider


class ContentFactory:
    """Enhanced content generation with multiple provider support"""

    def __init__(self, db=None):
        self.db = db
        # Unpack the cached providers and image generator
        self.providers, self.image_generator, self.multimodal_provider = _get_cached_providers()

    def generate_multimodal_content(self, messages: List[Dict[str, Any]], max_new_tokens: int = 300) -> Dict:
        """
        Public method to generate content from multimodal inputs using the Aya Vision provider.
        """
        if not self.multimodal_provider:
            raise RuntimeError("Aya Vision multimodal provider is not available.")

        try:
            result = self.multimodal_provider.generate_from_messages(messages, max_new_tokens)
            # You might want to log this usage to your database if needed
            return {
                "text": result["text"],
                "provider": "aya_vision",
                "cost_usd": result.get("usage", {}).get("cost_usd", 0.0),
                "tokens": result.get("usage", {}).get("output_tokens", 0)
            }
        except Exception as e:
            logger.error(f"Aya Vision generation failed: {e}")
            raise

    def generate_content(self, prompt: str, max_tokens: int = 500) -> Dict:
        """
        Public method to generate content using the best available provider.
        """
        return self._generate_with_fallback(prompt, max_tokens)

    def _generate_with_fallback(self, prompt: str, max_tokens: int = 500) -> Dict:
        """Try providers in priority order until one succeeds"""
        priority = ["groq", "cohere", "mistral", "kimi", "huggingface"]

        for provider_name in priority:
            provider = self.providers.get(provider_name)
            if provider is None:
                continue

            try:
                logger.info(f"Trying {provider_name}...")

                if provider_name == "cohere":
                    result = provider.generate_content(prompt, max_tokens)
                    if self.db:
                        self.db.log_api_usage("cohere", "generate_content", result.get("usage", {}).get("input_tokens", 0) + result.get("usage", {}).get("output_tokens", 0), result.get("usage", {}).get("cost_usd", 0.0))
                    return {"text": result["text"], "provider": provider_name, "cost_usd": result.get("usage", {}).get("cost_usd", 0.0), "tokens": result.get("usage", {}).get("output_tokens", 0)}
                elif provider_name == "groq":
                    result = provider.generate(prompt, max_tokens)
                    if self.db:
                        self.db.log_api_usage("groq", "generate", result.get("usage", {}).get("total_tokens", 0), result.get("cost_usd", 0.0))
                    return {"text": result["text"], "provider": provider_name, "cost_usd": result.get("cost_usd", 0.0), "tokens": result.get("usage", {}).get("completion_tokens", 0)}
                elif provider_name == "mistral":
                    result = provider.query_local(prompt)
                    return {"text": result["text"], "provider": provider_name, "cost_usd": 0.0, "tokens": 0}
                elif provider_name == "kimi":
                    result = provider.generate_content(prompt, max_tokens)
                    if self.db:
                        self.db.log_api_usage("kimi", "generate_content", result.get("usage", {}).get("total_tokens", 0), 0.0)
                    return {"text": result["text"], "provider": "kimi", "cost_usd": 0.0, "tokens": result.get("usage", {}).get("output_tokens", 0)}
                elif provider_name == "huggingface":
                    result = provider.generate(prompt, max_tokens)
                    return {"text": result["text"], "provider": provider_name, "cost_usd": 0.0, "tokens": 0}
            except Exception as e:
                logger.warning(f"{provider_name} failed: {e}")
                continue

        raise Exception("All content generation providers failed")

    def generate_social_pack(self, business_type: str, language: str = "afrikaans",
                            num_posts: int = 10, num_images: int = 5) -> Dict:
        """
        Generate a complete social media pack with REAL content by running text
        and image generation in parallel for improved performance.
        """
        logger.info(f"Generating social pack for {business_type} ({language}) using parallel execution.")

        posts_result = {}
        image_results: List[Dict[str, Any]] = []

        with ThreadPoolExecutor(max_workers=2) as executor:
            # Submit the text generation task
            posts_prompt = self._build_posts_prompt(business_type, language, num_posts)
            posts_future = executor.submit(self.generate_content, posts_prompt, max_tokens=2000)

            # Submit the image generation task
            if self.image_generator and num_images > 0:
                image_future = executor.submit(self.image_generator.generate_for_business, business_type, count=num_images)
            else:
                image_future = None

            # Retrieve results
            try:
                posts_result = posts_future.result()
            except Exception as e:
                logger.error(f"Content generation task failed: {e}")
                raise  # Re-raise the exception to be handled by the caller

            if image_future:
                try:
                    image_results = image_future.result()
                    logger.info(f"✅ Generated {len(image_results)} images")
                except Exception as e:
                    logger.error(f"Image generation task failed: {e}")
                    image_results = self._create_placeholder_images(num_images)
            else:
                image_results = self._create_placeholder_images(num_images)

        # Process the results after both tasks are complete
        posts = self._parse_posts(posts_result.get("text", ""), num_posts)
        total_cost = posts_result.get("cost_usd", 0.0)
        total_cost += sum(img.get("cost_usd", 0.0) for img in image_results)

        pack = {
            "posts": posts,
            "images": image_results,
            "metadata": {
                "business_type": business_type,
                "language": language,
                "generated_at": datetime.now().isoformat(),
                "provider": posts_result.get("provider"),
                "cost_usd": total_cost,
                "tokens_used": posts_result.get("tokens", 0)
            }
        }

        if self.db:
            self.db.save_content_pack(
                client_id="system",
                pack_data=pack,
                posts_count=len(posts),
                images_count=len(image_results),
                cost_usd=total_cost
            )

        logger.info(f"✅ Generated {len(posts)} posts and {len(image_results)} images")
        return pack

    def _build_posts_prompt(self, business_type: str, language: str, num_posts: int) -> str:
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

    def generate_email_sequence(self, business_name: str, business_type: str, days: int = 7) -> List[Dict]:
        prompt = f"""Generate a {days}-day email sequence for {business_name}, a {business_type} in South Africa.

Each email should include:
- Subject line (catchy, under 60 characters)
- Email body (150-250 words, engaging and valuable)
- Clear call-to-action

Format each email as:
DAY X:
SUBJECT: [subject line]
BODY: [email content]
---

Generate all {days} emails now:"""
        try:
            result = self.generate_content(prompt, max_tokens=2000)
            return self._parse_emails(result["text"], days)
        except Exception as e:
            logger.error(f"Email generation failed: {e}")
            return self._create_template_emails(business_name, days)

    def _parse_emails(self, text: str, expected_count: int) -> List[Dict]:
        emails = []
        current_email = {}
        lines = text.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("DAY "):
                if current_email:
                    emails.append(current_email)
                current_email = {"day": len(emails) + 1}
            elif line.startswith("SUBJECT:"):
                current_email["subject"] = line.replace("SUBJECT:", "").strip()
            elif line.startswith("BODY:"):
                current_email["body"] = line.replace("BODY:", "").strip()
            elif current_email.get("body") and line and not line.startswith("---"):
                current_email["body"] += "\n" + line
        if current_email:
            emails.append(current_email)
        return emails[:expected_count]

    def _create_template_emails(self, business_name: str, days: int) -> List[Dict]:
        templates = [{"subject": f"Welcome to {business_name}!", "body": f"Thank you for connecting with {business_name}. We're excited to serve you!"}, {"subject": f"Special Offer from {business_name}", "body": f"Check out our special offers this week at {business_name}!"}, {"subject": f"Tips & Tricks from {business_name}", "body": f"Here are some expert tips from the team at {business_name}."}]
        emails = []
        for i in range(days):
            template = templates[i % len(templates)]
            emails.append({"day": i + 1, "subject": template["subject"], "body": template["body"]})
        return emails

    def generate_mailchimp_campaign(self, business_name: str, pack: Dict) -> Dict:
        subject = f"Your Weekly Content Pack - {business_name}"
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; }}
                h1 {{ color: #2563eb; }}
                .post {{ margin: 20px 0; padding: 15px; border: 1px solid #e5e7eb; border-radius: 8px; }}
                .image {{ max-width: 100%; height: auto; margin: 10px 0; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; font-size: 12px; color: #6b7280; }}
            </style>
        </head>
        <body>
            <h1>Your Weekly Content Pack 🎉</h1>
            <p>Hello from {business_name}! Here's your fresh content for this week:</p>
        """
        for i, post in enumerate(pack.get("posts", [])[:5], 1):
            html_content += f"""
            <div class="post">
                <strong>Post {i}:</strong>
                <p>{post}</p>
            </div>
            """
        if pack.get("images"):
            html_content += "<h2>Your Images</h2>"
            for i, img in enumerate(pack["images"][:3], 1):
                html_content += f"""
                <div class="image-section">
                    <p><strong>Image {i}:</strong> {img.get('prompt', 'Business image')}</p>
                </div>
                """
        html_content += """
            <div class="footer">
                <p>Generated by Vaal AI Empire</p>
                <p>Questions? Contact us anytime!</p>
            </div>
        </body>
        </html>
        """
        return {"subject": subject, "html_content": html_content, "status": "created", "posts_included": len(pack.get("posts", [])), "images_included": len(pack.get("images", []))}

    def get_provider_status(self) -> Dict:
        return {provider: "available" if client else "unavailable" for provider, client in self.providers.items()}
