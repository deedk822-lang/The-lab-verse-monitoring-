from datetime import datetime, timedelta
from typing import Dict, List
import json
import logging

logger = logging.getLogger(__name__)

class RevenueTracker:
    """Track and analyze revenue metrics"""

    def __init__(self, db):
        self.db = db

    def daily_report(self) -> Dict:
        """Generate daily revenue report"""
        summary = self.db.get_revenue_summary(days=1)

        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "total_revenue": summary["total_revenue"],
            "clients_billed": summary["client_count"],
            "by_service": summary["by_service"]
        }

    def weekly_report(self) -> Dict:
        """Generate weekly revenue report"""
        summary = self.db.get_revenue_summary(days=7)

        return {
            "week_ending": datetime.now().strftime("%Y-%m-%d"),
            "total_revenue": summary["total_revenue"],
            "clients_billed": summary["client_count"],
            "avg_per_client": summary["total_revenue"] / max(summary["client_count"], 1),
            "by_service": summary["by_service"]
        }

    def monthly_projection(self) -> Dict:
        """Project monthly revenue based on current rate"""
        weekly = self.db.get_revenue_summary(days=7)
        weekly_revenue = weekly["total_revenue"]

        # Project to 4 weeks
        projected_monthly = weekly_revenue * 4

        return {
            "current_weekly": weekly_revenue,
            "projected_monthly": projected_monthly,
            "target": 25000,  # R25k first month target
            "on_track": projected_monthly >= 25000
        }

    def check_milestones(self):
        """Check for revenue milestones and trigger alerts"""
        from services.revenue_alert_bridge import RevenueAlertBridge
        
        summary = self.db.get_revenue_summary(days=30)
        prev_summary = self.db.get_revenue_summary(days=60) # Simplified prev period
        
        bridge = RevenueAlertBridge()
        metrics = bridge.format_metrics_from_db(summary, prev_summary)
        
        # Add top customers
        metrics["topPayingCustomers"] = self.db.get_top_customers(limit=5)
        
        return bridge.trigger_milestone_alert(metrics)

    def export_report(self, filepath: str = None) -> str:
        """Export comprehensive report to JSON"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "daily": self.daily_report(),
            "weekly": self.weekly_report(),
            "monthly_projection": self.monthly_projection()
        }

        if filepath:
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2)
            return filepath
        else:
            return json.dumps(report, indent=2)
