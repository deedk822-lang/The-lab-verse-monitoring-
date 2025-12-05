import unittest
import os
import sqlite3
from core.database import Database
from services.revenue_tracker import RevenueTracker
from services.content_scheduler import ContentScheduler

class TestVaalEmpire(unittest.TestCase):

    def setUp(self):
        self.db = Database(db_path="data/test_vaal_empire.db")
        self.revenue_tracker = RevenueTracker(self.db)
        self.scheduler = ContentScheduler(self.db)
        self.client_id = self.db.add_client({
            "name": "Test Client",
            "business_type": "Test Business",
            "phone": "1234567890"
        })

    def tearDown(self):
        os.remove("data/test_vaal_empire.db")

    def test_add_client(self):
        clients = self.db.get_active_clients()
        self.assertEqual(len(clients), 1)
        self.assertEqual(clients[0]["name"], "Test Client")

    def test_log_revenue(self):
        self.db.log_revenue(self.client_id, 100.0, "social_media")
        summary = self.db.get_revenue_summary(days=1)
        self.assertEqual(summary["total_revenue"], 100.0)
        self.assertEqual(summary["client_count"], 1)

    def test_schedule_pack(self):
        posts = ["post 1", "post 2"]
        self.scheduler.schedule_pack(self.client_id, posts)

        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM post_queue WHERE client_id = ?", (self.client_id,))
        scheduled_posts = cursor.fetchall()
        conn.close()

        self.assertEqual(len(scheduled_posts), 2)

    def test_get_client_by_id(self):
        client = self.db.get_client_by_id(self.client_id)
        self.assertIsNotNone(client)
        self.assertEqual(client["name"], "Test Client")

if __name__ == '__main__':
    unittest.main()
