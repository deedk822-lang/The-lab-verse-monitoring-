import logging
from datetime import datetime
from typing import Dict, List

logger = logging.getLogger(__name__)


class RevenueAnomalyDetector:
    """Detect anomalies in revenue patterns"""

    def __init__(self, db):
        self.db = db

    def detect_anomalies(self) -> List[Dict]:
        """
        Detect anomalies such as sudden drops in revenue
        Returns a list of detected anomalies with descriptions
        """
        anomalies = []

        # 1. Check for sudden drop in daily revenue
        daily_now = self.db.get_revenue_summary(days=1)["total_revenue"]
        daily_avg_7d = self.db.get_revenue_summary(days=7)["total_revenue"] / 7

        if daily_now < daily_avg_7d * 0.5 and daily_avg_7d > 100:
            anomalies.append(
                {
                    "type": "revenue_drop",
                    "severity": "high",
                    "message": f"Sudden revenue drop detected: R{daily_now} today vs R{daily_avg_7d:.2f} avg.",
                    "timestamp": datetime.now().isoformat(),
                }
            )

        # 2. Check for unusual client churn (no revenue from active clients)
        # This is a simplified check
        active_clients = self.db.get_active_clients()
        clients_with_revenue = self.db.get_revenue_summary(days=7)["client_count"]

        if len(active_clients) > 0 and clients_with_revenue < len(active_clients) * 0.3:
            anomalies.append(
                {
                    "type": "low_engagement",
                    "severity": "medium",
                    "message": f"Low client engagement: Only {clients_with_revenue}/{len(active_clients)} active clients billed in 7 days.",
                    "timestamp": datetime.now().isoformat(),
                }
            )

        return anomalies

    def run_check(self):
        """Run anomaly detection and log results"""
        anomalies = self.detect_anomalies()
        for anomaly in anomalies:
            logger.warning(f"ANOMALY DETECTED: {anomaly['message']}")
            # In a real system, this could trigger an immediate alert
        return anomalies
