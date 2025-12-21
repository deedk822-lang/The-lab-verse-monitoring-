#!/usr/bin/env python3
"""
Daily Automation Runner
Generates content, posts scheduled items, sends reports
"""

import schedule
import time
import logging
from datetime import datetime
from core.database import Database
from services.content_generator import get_content_factory
from services.content_scheduler import ContentScheduler
from services.social_poster import SocialPoster
from services.revenue_tracker import RevenueTracker

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/daily_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DailyAutomation:
    """Orchestrates all daily tasks"""

    def __init__(self):
        self.db = Database()
        self.factory = get_content_factory(self.db)
        self.scheduler = ContentScheduler(self.db)
        self.poster = SocialPoster()
        self.revenue = RevenueTracker(self.db)

    def generate_content_for_all_clients(self):
        """Generate content for all active clients"""
        logger.info("=== CONTENT GENERATION STARTED ===")

        clients = self.db.get_active_clients()
        logger.info(f"Found {len(clients)} active clients")

        for client in clients:
            try:
                # Check if client needs content this week
                # (simplified - in production, check last_delivery date)

                pack = self.factory.generate_social_pack(
                    client["business_type"],
                    client["language"]
                )

                # Schedule the posts
                self.scheduler.schedule_pack(client["id"], pack["posts"])

                logger.info(f"Generated and scheduled content for {client['name']}")

            except Exception as e:
                logger.error(f"Failed for {client['name']}: {e}")

        logger.info("=== CONTENT GENERATION COMPLETED ===")

    def post_scheduled_content(self):
        """Post all due content"""
        logger.info("=== POSTING SCHEDULED CONTENT ===")

        due_posts = self.scheduler.get_due_posts()
        logger.info(f"Found {len(due_posts)} posts due")

        for post in due_posts:
            try:
                platforms = post["platforms"].split(",")

                result = self.poster.post_via_ayrshare(
                    post["content"],
                    platforms,
                    post.get("image_url")
                )

                if result.get("status") != "error":
                    self.scheduler.mark_posted(post["id"])
                    logger.info(f"Posted content for client {post['client_id']}")

            except Exception as e:
                logger.error(f"Posting failed for post {post['id']}: {e}")

        logger.info("=== POSTING COMPLETED ===")

    def send_daily_report(self):
        """Generate and log daily report"""
        logger.info("=== DAILY REPORT ===")

        report = self.revenue.daily_report()
        logger.info(f"Revenue today: R{report['total_revenue']}")
        logger.info(f"Clients billed: {report['clients_billed']}")

        # Save report to file
        filepath = f"data/reports/daily_{datetime.now().strftime('%Y%m%d')}.json"
        self.revenue.export_report(filepath)
        logger.info(f"Report saved: {filepath}")

def run_scheduler():
    """Set up and run schedule"""
    automation = DailyAutomation()

    # Schedule tasks
    schedule.every().monday.at("06:00").do(automation.generate_content_for_all_clients)
    schedule.every().day.at("09:00").do(automation.post_scheduled_content)
    schedule.every().day.at("18:00").do(automation.send_daily_report)

    logger.info("Daily automation scheduler started")
    logger.info("Tasks:")
    logger.info("  - Content generation: Mondays at 06:00")
    logger.info("  - Post scheduled content: Daily at 09:00")
    logger.info("  - Daily report: Daily at 18:00")

    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    run_scheduler()
