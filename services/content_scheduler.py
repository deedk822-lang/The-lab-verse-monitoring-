from datetime import datetime, timedelta
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class ContentScheduler:
    """Schedule and manage social media posts"""

    def __init__(self, db):
        self.db = db

    def schedule_pack(self, client_id: str, posts: List[str], start_date: datetime = None) -> int:
        """Schedule a content pack for automatic posting"""
        if not start_date:
            start_date = datetime.now() + timedelta(days=1)


        posts_to_schedule = []
        for i, post_content in enumerate(posts):
            post_time = start_date + timedelta(days=i * 1.5)
            posts_to_schedule.append({
                "content": post_content,
                "platforms": "facebook,instagram",
                "scheduled_time": post_time.isoformat()
            })

        self.db.schedule_post_pack(client_id, posts_to_schedule)

        logger.info(f"Scheduled {len(posts_to_schedule)} posts for {client_id}")
        return len(posts_to_schedule)

    def get_due_posts(self) -> List[Dict]:
        """Get posts that are due to be published"""
        return self.db.get_due_posts()

    def mark_posted(self, post_id: int) -> bool:
        """Mark post as published"""
        self.db.mark_post_as_posted(post_id)
        return True
