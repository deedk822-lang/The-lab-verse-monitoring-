from typing import Dict, List, Optional
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class ContentFactory:
    """Enhanced content generation with lazy-loaded provider support"""

    def __init__(self, db=None):
        self.db = db
        self.provider_classes = self._discover_providers()
        self.provider_instances = {}  # Cache for initialized providers
        self.image_generator = None

        # Initialize image generation if available
        try:
            from api.image_generation import BusinessImageGenerator
            self.image_generator = BusinessImageGenerator()
            logger.info("✅ Image generation enabled")
        except Exception as e:
            logger.warning(f"⚠️  Image generation disabled: {e}")

    def _discover_providers(self) -> Dict:
        """Discover all available content generation provider classes"""
        provider_classes = {}
        # Try Cohere
        try:
            from api.cohere import CohereAPI
            provider_classes["cohere"] = CohereAPI
        except (ImportError, ValueError):
            pass
        # Try Groq
        try:
            from api.groq_api import GroqAPI
            provider_classes["groq"] = GroqAPI
        except (ImportError, ValueError):
            pass
        # Try Mistral (local via Ollama)
        try:
            from api.mistral import MistralAPI
            provider_classes["mistral"] = MistralAPI
        except (ImportError, ValueError):
            pass
        # Try HuggingFace
        try:
            from api.huggingface_api import HuggingFaceAPI
            provider_classes["huggingface"] = HuggingFaceAPI
        except (ImportError, ValueError):
            pass

        logger.info(f"Discovered providers: {', '.join(provider_classes.keys())}")
        return provider_classes

    def get_provider(self, provider_name: str):
        """Lazy-load a provider instance on first use"""
        if provider_name in self.provider_instances:
            return self.provider_instances[provider_name]

        if provider_name in self.provider_classes:
            try:
                logger.info(f"Initializing {provider_name} provider...")
                instance = self.provider_classes[provider_name]()
                self.provider_instances[provider_name] = instance
                logger.info(f"✅ {provider_name} provider initialized")
                return instance
            except Exception as e:
                logger.warning(f"⚠️  Failed to initialize {provider_name}: {e}")
                # Remove from available providers to prevent re-initialization attempts
                self.provider_classes.pop(provider_name, None)
                return None
        return None

    def _generate_with_fallback(self, prompt: str, max_tokens: int = 500) -> Dict:
        """Try providers in priority order until one succeeds"""
        priority = ["groq", "cohere", "mistral", "huggingface"]

        for provider_name in priority:
            provider = self.get_provider(provider_name)
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
        """Get the detailed status of all discovered providers."""
        status = {}
        # Iterate over a fixed list of known providers to ensure consistent output
        for provider_name in ["cohere", "groq", "mistral", "huggingface"]:
            if provider_name in self.provider_instances:
                # The provider has been successfully initialized and is ready.
                status[provider_name] = "initialized"
            elif provider_name in self.provider_classes:
                # The provider's class was discovered but it has not been used yet.
                status[provider_name] = "available"
            else:
                # The provider's class could not be imported or failed to initialize.
                status[provider_name] = "unavailable"
        return status
