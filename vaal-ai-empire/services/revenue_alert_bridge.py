import os
import json
import requests
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

class RevenueAlertBridge:
    """Bridge between Python revenue tracking and TypeScript alert engine"""

    def __init__(self, alert_engine_url: str = None):
        self.alert_engine_url = alert_engine_url or os.getenv("REVENUE_ALERT_WEBHOOK_URL")
        
    def trigger_milestone_alert(self, metrics: Dict[str, Any]) -> bool:
        """
        Trigger a revenue milestone alert via the alert engine webhook
        
        Expected metrics format:
        {
            "currentMrr": float,
            "previousMrr": float,
            "growthRate": float,
            "customerCount": int,
            "avgRevenuePerCustomer": float,
            "topPayingCustomers": [{"name": str, "amount": float}]
        }
        """
        if not self.alert_engine_url:
            logger.warning("REVENUE_ALERT_WEBHOOK_URL not configured. Skipping alert.")
            return False

        try:
            response = requests.post(
                self.alert_engine_url,
                json=metrics,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            response.raise_for_status()
            logger.info(f"Successfully triggered revenue milestone alert for MRR: {metrics['currentMrr']}")
            return True
        except Exception as e:
            logger.error(f"Failed to trigger revenue milestone alert: {e}")
            return False

    @staticmethod
    def format_metrics_from_db(summary: Dict[str, Any], previous_summary: Dict[str, Any] = None) -> Dict[str, Any]:
        """Format database summary into the format expected by the alert engine"""
        current_mrr = summary.get("total_revenue", 0)
        previous_mrr = previous_summary.get("total_revenue", 0) if previous_summary else current_mrr * 0.9 # Fallback
        
        growth_rate = ((current_mrr - previous_mrr) / max(previous_mrr, 1)) * 100
        
        return {
            "currentMrr": current_mrr,
            "previousMrr": previous_mrr,
            "growthRate": growth_rate,
            "customerCount": summary.get("client_count", 0),
            "avgRevenuePerCustomer": current_mrr / max(summary.get("client_count", 1), 1),
            "topPayingCustomers": [] # Would need a separate DB call to populate
        }
