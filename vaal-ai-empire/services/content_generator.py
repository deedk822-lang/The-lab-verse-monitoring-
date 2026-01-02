from typing import Dict, List, Optional
import logging
import json
from datetime import datetime

import importlib

logger = logging.getLogger(__name__)


class ProviderFactory:
    """
    ⚡ Bolt Optimization: Lazy-loads and caches AI content providers.
    This prevents all API clients from being initialized on every
    ContentFactory instantiation, significantly speeding up the process.
    """
    _provider_cache: Dict[str, Optional[object]] = {}
    _provider_map: Dict[str, tuple[str, str]] = {
        "cohere": ("api.cohere", "CohereAPI"),
        "groq": ("api.groq_api", "GroqAPI"),
        "mistral": ("api.mistral", "MistralAPI"),
        "huggingface": ("api.huggingface_api", "HuggingFaceAPI"),
    }

    @classmethod
    def get_provider(cls, provider_name: str) -> Optional[object]:
        """On-demand initializes and returns a provider instance."""
        # Return from cache if already initialized
        if provider_name in cls._provider_cache:
            return cls._provider_cache[provider_name]

        if provider_name not in cls._provider_map:
            logger.warning(f"Provider '{provider_name}' not recognized.")
            return None

        # Dynamically import and instantiate the provider
        try:
            module_path, class_name = cls._provider_map[provider_name]
            module = importlib.import_module(module_path)
            provider_class = getattr(module, class_name)
            instance = provider_class()

            cls._provider_cache[provider_name] = instance
            logger.info(f"✅ {provider_name.capitalize()} provider lazy-loaded and initialized.")
            return instance
        except (ImportError, AttributeError, ValueError) as e:
            # Cache the failure to prevent repeated attempts
            cls._provider_cache[provider_name] = None
            logger.warning(f"⚠️  {provider_name.capitalize()} unavailable on first use: {e}")
            return None


class ContentFactory:
    """Enhanced content generation with multiple provider support"""

    def __init__(self, db=None):
        self.db = db
        # ⚡ Bolt Optimization: Replaced eager initialization with a lazy-loading factory.
        # self.providers = self._initialize_providers()
        self.provider_factory = ProviderFactory()
        self.image_generator = None

        # Initialize image generation if available
        try:
            from api.image_generation import BusinessImageGenerator
            self.image_generator = BusinessImageGenerator()
            logger.info("✅ Image generation enabled")
        except Exception as e:
            logger.warning(f"⚠️  Image generation disabled: {e}")

    def _generate_with_fallback(self, prompt: str, max_tokens: int = 500) -> Dict:
        """Try providers in priority order until one succeeds"""
        priority = ["groq", "cohere", "mistral", "huggingface"]

        for provider_name in priority:
            # ⚡ Bolt Optimization: Get provider on-demand instead of from a pre-initialized dict.
            provider = self.provider_factory.get_provider(provider_name)
            if provider is None:
                continue

            try:
                logger.info(f"Trying {provider_name}...")

                if provider_name == "cohere":
                    result = provider.generate_content(prompt, max_tokens)

                    # Log usage
                    if self.db:
                        self.db.log_api_usage(
                            "cohere",
                            "generate_content",
                            result.get("usage", {}).get("input_tokens", 0) +
                            result.get("usage", {}).get("output_tokens", 0),
                            result.get("usage", {}).get("cost_usd", 0.0)
                        )

                    return {
                        "text": result["text"],
                        "provider": provider_name,
                        "cost_usd": result.get("usage", {}).get("cost_usd", 0.0),
                        "tokens": result.get("usage", {}).get("output_tokens", 0)
                    }

                elif provider_name == "groq":
                    result = provider.generate(prompt, max_tokens)

                    if self.db:
                        self.db.log_api_usage(
                            "groq",
                            "generate",
                            result.get("usage", {}).get("total_tokens", 0),
                            result.get("cost_usd", 0.0)
                        )

                    return {
                        "text": result["text"],
                        "provider": provider_name,
                        "cost_usd": result.get("cost_usd", 0.0),
                        "tokens": result.get("usage", {}).get("completion_tokens", 0)
                    }

                elif provider_name == "mistral":
                    result = provider.query_local(prompt)

                    return {
                        "text": result["text"],
                        "provider": provider_name,
                        "cost_usd": 0.0,  # Local, no cost
                        "tokens": 0
                    }

                elif provider_name == "huggingface":
                    result = provider.generate(prompt, max_tokens)

                    return {
                        "text": result["text"],
                        "provider": provider_name,
                        "cost_usd": 0.0,  # Free tier
                        "tokens": 0
                    }

            except Exception as e:
                logger.warning(f"{provider_name} failed: {e}")
                continue

        # All providers failed
        raise Exception("All content generation providers failed")

    def generate_social_pack(self, business_type: str, language: str = "afrikaans",
                            num_posts: int = 10, num_images: int = 5) -> Dict:
        """Generate complete social media pack with REAL content"""

        logger.info(f"Generating social pack for {business_type} ({language})")

        try:
            # Generate posts
            posts_prompt = self._build_posts_prompt(business_type, language, num_posts)
            posts_result = self._generate_with_fallback(posts_prompt, max_tokens=2000)

            # Parse posts from response
            posts = self._parse_posts(posts_result["text"], num_posts)

            # Generate images if available
            images = []
            if self.image_generator:
                try:
                    image_results = self.image_generator.generate_for_business(
                        business_type,
                        count=num_images
                    )
                    images = image_results
                    logger.info(f"✅ Generated {len(images)} images")
                except Exception as e:
                    logger.error(f"Image generation failed: {e}")
                    images = self._create_placeholder_images(num_images)
            else:
                images = self._create_placeholder_images(num_images)

            # Calculate total cost
            total_cost = posts_result.get("cost_usd", 0.0)
            total_cost += sum(img.get("cost_usd", 0.0) for img in images)

            pack = {
                "posts": posts,
                "images": images,
                "metadata": {
                    "business_type": business_type,
                    "language": language,
                    "generated_at": datetime.now().isoformat(),
                    "provider": posts_result.get("provider"),
                    "cost_usd": total_cost,
                    "tokens_used": posts_result.get("tokens", 0)
                }
            }

            # Save to database if available
            if self.db:
                self.db.save_content_pack(
                    client_id="system",
                    pack_data=pack,
                    posts_count=len(posts),
                    images_count=len(images),
                    cost_usd=total_cost
                )

            logger.info(f"✅ Generated {len(posts)} posts and {len(images)} images")
            return pack

        except Exception as e:
            logger.error(f"Content generation failed: {e}")
            raise e

    def _build_posts_prompt(self, business_type: str, language: str, num_posts: int) -> str:
        """Build optimized prompt for post generation"""

        language_instructions = {
            "afrikaans": "Write in Afrikaans (South African dialect)",
            "english": "Write in English (South African style)",
            "both": "Write 50% in Afrikaans, 50% in English"
        }

        lang_instruction = language_instructions.get(language, language_instructions["afrikaans"])

        business_contexts = {
            "butchery": "a local butchery in Vaal Triangle, South Africa. Focus on fresh meat, quality cuts, special offers, and traditional braai culture.",
            "auto_repair": "an auto repair shop in Vaal Triangle, South Africa. Focus on reliable service, quality parts, professional mechanics, and vehicle maintenance tips.",
            "cafe": "a coffee shop in Vaal Triangle, South Africa. Focus on fresh coffee, baked goods, cozy atmosphere, and community gathering.",
            "restaurant": "a restaurant in Vaal Triangle, South Africa. Focus on delicious food, specials, events, and dining experience.",
            "salon": "a hair and beauty salon in Vaal Triangle, South Africa. Focus on latest styles, professional service, beauty tips, and special treatments.",
            "retail": "a retail store in Vaal Triangle, South Africa. Focus on product quality, special offers, customer service, and new arrivals."
        }

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
        """Parse generated text into individual posts"""
        # Try splitting by separator
        if "---" in text:
            posts = [p.strip() for p in text.split("---") if p.strip()]
        else:
            # Split by double newline
            posts = [p.strip() for p in text.split("\n\n") if p.strip()]

        # Clean up posts
        cleaned_posts = []
        for post in posts:
            # Remove numbering if present
            post = post.split(".", 1)[-1].strip() if post[0].isdigit() else post

            # Remove "Post X:" prefix if present
            if post.lower().startswith("post "):
                post = post.split(":", 1)[-1].strip() if ":" in post else post

            if len(post) > 30:  # Ensure it's substantive
                cleaned_posts.append(post)

        # If we don't have enough posts, generate more or pad
        while len(cleaned_posts) < expected_count:
            if cleaned_posts:
                # Slight variation of existing post
                base_post = cleaned_posts[len(cleaned_posts) % len(cleaned_posts)]
                cleaned_posts.append(base_post + " 🌟")
            else:
                cleaned_posts.append("Coming soon! Stay tuned for exciting updates. 🎉")

        return cleaned_posts[:expected_count]

    def _create_placeholder_images(self, count: int) -> List[Dict]:
        """Create placeholder image references"""
        return [{
            "prompt": f"Business image {i+1}",
            "image_url": f"https://via.placeholder.com/800x600?text=Image+{i+1}",
            "provider": "placeholder",
            "cost_usd": 0.0
        } for i in range(count)]

    def generate_email_sequence(self, business_name: str, business_type: str,
                               days: int = 7) -> List[Dict]:
        """Generate email sequence for MailChimp"""

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
            result = self._generate_with_fallback(prompt, max_tokens=2000)
            emails = self._parse_emails(result["text"], days)

            return emails

        except Exception as e:
            logger.error(f"Email generation failed: {e}")
            # Return basic template
            return self._create_template_emails(business_name, days)

    def _parse_emails(self, text: str, expected_count: int) -> List[Dict]:
        """Parse email sequence from generated text"""
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
        """Create template emails as fallback"""
        templates = [
            {
                "subject": f"Welcome to {business_name}!",
                "body": f"Thank you for connecting with {business_name}. We're excited to serve you!"
            },
            {
                "subject": f"Special Offer from {business_name}",
                "body": f"Check out our special offers this week at {business_name}!"
            },
            {
                "subject": f"Tips & Tricks from {business_name}",
                "body": f"Here are some expert tips from the team at {business_name}."
            }
        ]

        emails = []
        for i in range(days):
            template = templates[i % len(templates)]
            emails.append({
                "day": i + 1,
                "subject": template["subject"],
                "body": template["body"]
            })

        return emails

    def generate_mailchimp_campaign(self, business_name: str, pack: Dict) -> Dict:
        """Create MailChimp campaign HTML from content pack"""
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

        # Add posts
        for i, post in enumerate(pack.get("posts", [])[:5], 1):
            html_content += f"""
            <div class="post">
                <strong>Post {i}:</strong>
                <p>{post}</p>
            </div>
            """

        # Add images section
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

        return {
            "subject": subject,
            "html_content": html_content,
            "status": "created",
            "posts_included": len(pack.get("posts", [])),
            "images_included": len(pack.get("images", []))
        }

    def get_provider_status(self) -> Dict:
        """
        ⚡ Bolt Fix: Restore original method contract to avoid breaking changes.
        This method now actively initializes all providers to give a definitive
        "available" or "unavailable" status, matching the old behavior.
        The performance benefit of lazy loading is retained for all other
        operations.
        """
        status = {}
        known_providers = self.provider_factory._provider_map.keys()
        for provider_name in known_providers:
            # This will trigger initialization if not already cached
            provider = self.provider_factory.get_provider(provider_name)
            status[provider_name] = "available" if provider else "unavailable"
        return status