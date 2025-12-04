import logging

logger = logging.getLogger(__name__)

class ContentFactory:
    """Mock content factory"""
    def generate_social_pack(self, business_type: str, language: str) -> dict:
        logger.info(f"Generating social pack for {business_type} in {language}")
        return {
            "posts": [
                "This is a mock post.",
                "This is another mock post."
            ],
            "images": [
                "https://via.placeholder.com/1080",
                "https://via.placeholder.com/1080"
            ]
        }
