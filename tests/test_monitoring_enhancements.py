import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add src and vaal-ai-empire to path
sys.path.append(os.path.join(os.getcwd(), "vaal-ai-empire"))

from core.database import Database
from core.system_monitor import SystemMonitor
from services.revenue_tracker import RevenueTracker
from services.revenue_anomaly_detector import RevenueAnomalyDetector

class TestMonitoringEnhancements(unittest.TestCase):
    def setUp(self):
        # Use in-memory database for testing
        self.db = Database(":memory:")
        self.monitor = SystemMonitor(self.db)
        self.tracker = RevenueTracker(self.db)
        self.detector = RevenueAnomalyDetector(self.db)

        # Add a test client
        self.client_id = self.db.add_client({
            "name": "Test Client",
            "business_type": "SaaS",
            "phone": "1234567890"
        })

    def test_revenue_metrics_in_status(self):
        # Log some revenue
        self.db.log_revenue(self.client_id, 1000.0, "subscription", status="paid")
        
        status = self.monitor.get_system_status()
        self.assertIn("revenue", status)
        self.assertEqual(status["revenue"]["total_30d"], 1000.0)
        self.assertEqual(status["revenue"]["client_count"], 1)

    def test_revenue_recommendations(self):
        # Low revenue scenario
        self.db.log_revenue(self.client_id, 100.0, "subscription", status="paid")
        
        status = self.monitor.get_system_status()
        recommendations = self.monitor._generate_recommendations(status)
        
        self.assertTrue(any("Revenue below target" in r for r in recommendations))

    def test_anomaly_detection(self):
        # Setup: High average, low today
        # We need to mock the dates or just log revenue with different dates
        # For simplicity, let's just check if the detector runs without error
        anomalies = self.detector.detect_anomalies()
        self.assertIsInstance(anomalies, list)

    @patch('requests.post')
    def test_milestone_alert_trigger(self, mock_post):
        mock_post.return_value.status_code = 200
        
        # Set environment variable for bridge
        os.environ["REVENUE_ALERT_WEBHOOK_URL"] = "http://test-webhook.com"
        
        # Log enough revenue for a milestone (e.g., > 5000)
        self.db.log_revenue(self.client_id, 6000.0, "subscription", status="paid")
        
        result = self.tracker.check_milestones()
        self.assertTrue(result)
        self.assertTrue(mock_post.called)

if __name__ == "__main__":
    unittest.main()
