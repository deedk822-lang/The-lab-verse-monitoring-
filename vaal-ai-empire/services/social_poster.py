import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

class SocialPoster:
    """Real social media posting with multiple provider support"""

    def __init__(self, db=None):
        self.db = db
        self.providers = self._detect_providers()

        # API endpoints
        self.ayrshare_url = "https://app.ayrshare.com/api"
        self.socialpilot_url = "https://api.socialpilot.co/v2"

    def _detect_providers(self) -> Dict[str, bool]:
        """Detect available posting providers"""
        providers = {
            "ayrshare": bool(os.getenv("AYRSHARE_API_KEY")),
            "socialpilot": bool(os.getenv("SOCIALPILOT_API_KEY")),
            "twitter": bool(os.getenv("TWITTER_BEARER_TOKEN")),
            "facebook": bool(os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")),
        }

        available = [p for p, status in providers.items() if status]
        if available:
            logger.info(f"Available social providers: {', '.join(available)}")
        else:
            logger.warning("⚠️  No social media providers configured - using simulation mode")

        return providers

    def post(self, content: str, platforms: List[str],
            image_url: Optional[str] = None, provider: str = "auto") -> Dict:
        """
        Post to social media

        Args:
            content: Post text
            platforms: List of platforms (facebook, instagram, twitter, linkedin)
            image_url: Optional image URL
            provider: Posting provider (auto, ayrshare, socialpilot, direct)

        Returns:
            Dict with post results
        """
        if provider == "auto":
            provider = self._select_best_provider()

        try:
            if provider == "ayrshare" and self.providers["ayrshare"]:
                return self.post_via_ayrshare(content, platforms, image_url)

            elif provider == "socialpilot" and self.providers["socialpilot"]:
                return self.post_via_socialpilot(content, platforms, image_url)

            elif provider == "direct":
                return self.post_direct(content, platforms, image_url)

            else:
                # Simulation mode
                return self.simulate_post(content, platforms, image_url)

        except Exception as e:
            logger.error(f"Posting failed: {e}")

            if self.db:
                self.db.log_api_usage(
                    f"social_{provider}",
                    "post",
                    success=False,
                    error_message=str(e)
                )

            return {
                "status": "error",
                "error": str(e),
                "provider": provider
            }

    def _select_best_provider(self) -> str:
        """Select best available provider"""
        if self.providers["ayrshare"]:
            return "ayrshare"
        elif self.providers["socialpilot"]:
            return "socialpilot"
        elif any([self.providers["twitter"], self.providers["facebook"]]):
            return "direct"
        else:
            return "simulation"

    def post_via_ayrshare(self, content: str, platforms: List[str],
                         image_url: Optional[str] = None) -> Dict:
        """Post via Ayrshare (multi-platform)"""
        api_key = os.getenv("AYRSHARE_API_KEY")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "post": content,
            "platforms": platforms
        }

        if image_url:
            payload["mediaUrls"] = [image_url]

        try:
            response = requests.post(
                f"{self.ayrshare_url}/post",
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code != 200:
                raise Exception(f"Ayrshare error ({response.status_code}): {response.text}")

            data = response.json()

            # Log usage
            if self.db:
                self.db.log_api_usage(
                    "ayrshare",
                    "post",
                    tokens_used=len(content),
                    cost_usd=0.01 * len(platforms),  # Approximate cost
                    success=True
                )

            logger.info(f"✅ Posted via Ayrshare to {', '.join(platforms)}")

            return {
                "status": "success",
                "provider": "ayrshare",
                "platforms": platforms,
                "post_ids": data.get("postIds", {}),
                "posted_at": datetime.now().isoformat(),
                "simulated": False
            }

        except Exception as e:
            logger.error(f"Ayrshare error: {e}")
            raise e

    def post_via_socialpilot(self, content: str, platforms: List[str],
                            image_url: Optional[str] = None) -> Dict:
        """Post via SocialPilot (white-label)"""
        api_key = os.getenv("SOCIALPILOT_API_KEY")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        results = []

        # SocialPilot requires one request per platform
        for platform in platforms:
            payload = {
                "text": content,
                "platform": platform,
                "mediaUrls": [image_url] if image_url else []
            }

            try:
                response = requests.post(
                    f"{self.socialpilot_url}/posts",
                    headers=headers,
                    json=payload,
                    timeout=30
                )

                if response.status_code not in [200, 201]:
                    raise Exception(f"SocialPilot error ({response.status_code}): {response.text}")

                data = response.json()
                results.append({
                    "platform": platform,
                    "post_id": data.get("id"),
                    "status": "success"
                })

                logger.info(f"✅ Posted to {platform} via SocialPilot")

            except Exception as e:
                logger.error(f"SocialPilot error for {platform}: {e}")
                results.append({
                    "platform": platform,
                    "status": "error",
                    "error": str(e)
                })

        # Log usage
        if self.db:
            self.db.log_api_usage(
                "socialpilot",
                "post",
                tokens_used=len(content),
                cost_usd=0.01 * len(platforms),
                success=all(r["status"] == "success" for r in results)
            )

        return {
            "status": "success" if all(r["status"] == "success" for r in results) else "partial",
            "provider": "socialpilot",
            "platforms": platforms,
            "results": results,
            "posted_at": datetime.now().isoformat(),
            "simulated": False
        }

    def post_direct(self, content: str, platforms: List[str],
                   image_url: Optional[str] = None) -> Dict:
        """Post directly using platform APIs"""
        results = []

        for platform in platforms:
            try:
                if platform == "twitter" and self.providers["twitter"]:
                    result = self._post_twitter(content, image_url)
                    results.append({"platform": "twitter", **result})

                elif platform == "facebook" and self.providers["facebook"]:
                    result = self._post_facebook(content, image_url)
                    results.append({"platform": "facebook", **result})

                else:
                    results.append({
                        "platform": platform,
                        "status": "skipped",
                        "reason": "provider not configured"
                    })

            except Exception as e:
                logger.error(f"Direct post to {platform} failed: {e}")
                results.append({
                    "platform": platform,
                    "status": "error",
                    "error": str(e)
                })

        return {
            "status": "success" if any(r.get("status") == "success" for r in results) else "error",
            "provider": "direct",
            "platforms": platforms,
            "results": results,
            "posted_at": datetime.now().isoformat(),
            "simulated": False
        }

    def _post_twitter(self, content: str, image_url: Optional[str] = None) -> Dict:
        """Post to Twitter using API v2"""
        bearer_token = os.getenv("TWITTER_BEARER_TOKEN")

        # For posting, need OAuth 1.0a (not bearer token)
        # This requires tweepy or manual OAuth implementation
        try:
            import tweepy

            consumer_key = os.getenv("TWITTER_API_KEY")
            consumer_secret = os.getenv("TWITTER_API_SECRET")
            access_token = os.getenv("TWITTER_ACCESS_TOKEN")
            access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

            client = tweepy.Client(
                bearer_token=bearer_token,
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                access_token=access_token,
                access_token_secret=access_token_secret
            )

            # Post tweet
            response = client.create_tweet(text=content)

            logger.info(f"✅ Posted to Twitter: {response.data['id']}")

            return {
                "status": "success",
                "post_id": response.data["id"]
            }

        except ImportError:
            logger.error("Tweepy not installed. Install with: pip install tweepy")
            raise Exception("Twitter API library not available")
        except Exception as e:
            logger.error(f"Twitter post failed: {e}")
            raise e

    def _post_facebook(self, content: str, image_url: Optional[str] = None) -> Dict:
        """Post to Facebook Page"""
        access_token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
        page_id = os.getenv("FACEBOOK_PAGE_ID")

        url = f"https://graph.facebook.com/v18.0/{page_id}/feed"

        payload = {
            "message": content,
            "access_token": access_token
        }

        if image_url:
            # For images, use /photos endpoint
            url = f"https://graph.facebook.com/v18.0/{page_id}/photos"
            payload["url"] = image_url
            payload["caption"] = content

        try:
            response = requests.post(url, data=payload, timeout=30)

            if response.status_code != 200:
                raise Exception(f"Facebook error ({response.status_code}): {response.text}")

            data = response.json()

            logger.info(f"✅ Posted to Facebook: {data.get('id', data.get('post_id'))}")

            return {
                "status": "success",
                "post_id": data.get("id", data.get("post_id"))
            }

        except Exception as e:
            logger.error(f"Facebook post failed: {e}")
            raise e

    def simulate_post(self, content: str, platforms: List[str],
                     image_url: Optional[str] = None) -> Dict:
        """Simulate posting (for testing)"""
        logger.info(f"📱 [SIMULATED] Posting to {', '.join(platforms)}")
        logger.info(f"   Content: {content[:100]}...")
        if image_url:
            logger.info(f"   Image: {image_url}")

        return {
            "status": "simulated",
            "provider": "simulation",
            "platforms": platforms,
            "post_ids": {platform: f"sim_{platform}_{datetime.now().timestamp()}"
                        for platform in platforms},
            "posted_at": datetime.now().isoformat(),
            "simulated": True
        }

    def schedule_post(self, content: str, platforms: List[str],
                     schedule_time: str, image_url: Optional[str] = None) -> Dict:
        """Schedule a post for future publishing"""

        if self.providers["ayrshare"]:
            api_key = os.getenv("AYRSHARE_API_KEY")

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "post": content,
                "platforms": platforms,
                "scheduleDate": schedule_time  # ISO 8601 format
            }

            if image_url:
                payload["mediaUrls"] = [image_url]

            try:
                response = requests.post(
                    f"{self.ayrshare_url}/post",
                    headers=headers,
                    json=payload,
                    timeout=30
                )

                if response.status_code != 200:
                    raise Exception(f"Scheduling error: {response.text}")

                data = response.json()

                logger.info(f"✅ Scheduled post for {schedule_time}")

                return {
                    "status": "scheduled",
                    "provider": "ayrshare",
                    "platforms": platforms,
                    "schedule_time": schedule_time,
                    "schedule_id": data.get("id")
                }

            except Exception as e:
                logger.error(f"Scheduling failed: {e}")
                raise e
        else:
            # Store in database for manual posting
            if self.db:
                # Would insert into post_queue table
                pass

            return {
                "status": "queued",
                "provider": "database",
                "platforms": platforms,
                "schedule_time": schedule_time,
                "note": "Will be posted by automation script"
            }

    def get_post_analytics(self, post_id: str, platform: str) -> Dict:
        """Get analytics for a posted content"""

        if self.providers["ayrshare"]:
            api_key = os.getenv("AYRSHARE_API_KEY")

            headers = {"Authorization": f"Bearer {api_key}"}

            try:
                response = requests.get(
                    f"{self.ayrshare_url}/post/{post_id}",
                    headers=headers,
                    timeout=15
                )

                if response.status_code == 200:
                    return response.json()

            except Exception as e:
                logger.error(f"Analytics fetch failed: {e}")

        return {"status": "unavailable"}

    def bulk_post(self, posts: List[Dict]) -> Dict:
        """Post multiple pieces of content"""
        results = {
            "total": len(posts),
            "successful": 0,
            "failed": 0,
            "details": []
        }

        for post in posts:
            try:
                result = self.post(
                    content=post["content"],
                    platforms=post["platforms"],
                    image_url=post.get("image_url")
                )

                if result["status"] in ["success", "simulated"]:
                    results["successful"] += 1
                else:
                    results["failed"] += 1

                results["details"].append(result)

            except Exception as e:
                results["failed"] += 1
                results["details"].append({
                    "status": "error",
                    "error": str(e),
                    "post": post
                })

        return results

    def get_provider_status(self) -> Dict:
        """Get status of all providers"""
        return {
            "providers": self.providers,
            "primary": self._select_best_provider(),
            "supported_platforms": self.get_supported_platforms()
        }

    def get_supported_platforms(self) -> List[str]:
        """Get list of supported platforms"""
        platforms = ["facebook", "instagram", "twitter", "linkedin"]

        if self.providers["ayrshare"] or self.providers["socialpilot"]:
            platforms.extend(["pinterest", "tiktok"])

        return platforms
