from datetime import datetime, timedelta
from typing import List, Dict
import logging
import sqlite3

logger = logging.getLogger(__name__)

class ContentScheduler:
    """Schedule and manage social media posts"""

    def __init__(self, db):
        self.db = db

    def schedule_pack(self, client_id: str, posts: List[str], start_date: datetime = None) -> int:
        """Schedule a content pack for automatic posting"""
        if not start_date:
            start_date = datetime.now() + timedelta(days=1)

        scheduled_count = 0

        # Schedule posts over 30 days (1 post every 1.5 days)
        for i, post in enumerate(posts):
            post_time = start_date + timedelta(days=i * 1.5)

            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO post_queue (client_id, content, platforms, scheduled_time)
                VALUES (?, ?, ?, ?)
            """, (client_id, post, "facebook,instagram", post_time.isoformat()))

            conn.commit()
            conn.close()
            scheduled_count += 1

        logger.info(f"Scheduled {scheduled_count} posts for {client_id}")
        return scheduled_count

    def get_due_posts(self) -> List[Dict]:
        """Get posts that are due to be published"""
        conn = sqlite3.connect(self.db.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM post_queue
            WHERE posted = 0
            AND datetime(scheduled_time) <= datetime('now')
            ORDER BY scheduled_time
            LIMIT 50
        """)

        posts = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return posts

    def mark_posted(self, post_id: int) -> bool:
        """Mark post as published"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE post_queue
            SET posted = 1, posted_at = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), post_id))

        conn.commit()
        conn.close()

        return True
