import requests
import os
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class SocialPoster:
    """Post content to social media platforms"""

    def __init__(self):
        self.ayrshare_key = os.getenv("AYRSHARE_API_KEY")
        self.socialpilot_key = os.getenv("SOCIALPILOT_API_KEY")

    def post_via_ayrshare(self, content: str, platforms: List[str], image_url: str = None) -> Dict:
        """Post via Ayrshare (multi-platform)"""
        if not self.ayrshare_key:
            logger.info(f"[MOCK] Would post to {platforms}: {content[:50]}...")
            return {"status": "mock", "post_ids": ["mock_123"]}

        try:
            response = requests.post(
                "https://app.ayrshare.com/api/post",
                headers={"Authorization": f"Bearer {self.ayrshare_key}"},
                json={
                    "post": content,
                    "platforms": platforms,
                    "mediaUrls": [image_url] if image_url else []
                }
            )

            return response.json()
        except Exception as e:
            logger.error(f"Ayrshare error: {e}")
            return {"status": "error", "message": str(e)}

    def post_via_socialpilot(self, content: str, platform: str, image_url: str = None) -> Dict:
        """Post via SocialPilot (white-label)"""
        if not self.socialpilot_key:
            logger.info(f"[MOCK] Would post to {platform}: {content[:50]}...")
            return {"status": "mock", "post_id": "mock_456"}

        try:
            response = requests.post(
                "https://api.socialpilot.co/v2/posts",
                headers={"Authorization": f"Bearer {self.socialpilot_key}"},
                json={
                    "text": content,
                    "platform": platform,
                    "media": [image_url] if image_url else []
                }
            )

            return response.json()
        except Exception as e:
            logger.error(f"SocialPilot error: {e}")
            return {"status": "error", "message": str(e)}
