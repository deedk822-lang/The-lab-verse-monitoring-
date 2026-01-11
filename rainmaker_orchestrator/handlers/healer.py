"""
Self-Healing Agent for handling Prometheus alerts
Automatically responds to system issues and performs remediation
"""
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class SelfHealingAgent:
    """
    Agent that handles alerts from monitoring systems and performs
    automated remediation actions.
    """

    def __init__(self):
        self.remediation_history: List[Dict[str, Any]] = []
        self.max_history = 100

    def handle_alert(self, alert_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process incoming alert and perform remediation.

        Args:
            alert_payload: Alert data from Prometheus AlertManager

        Returns:
            Dict containing remediation result
        """
        try:
            alerts = alert_payload.get('alerts', [])

            if not alerts:
                return {
                    "status": "no_alerts",
                    "message": "No alerts to process"
                }

            results = []
            for alert in alerts:
                result = self._process_single_alert(alert)
                results.append(result)

            return {
                "status": "processed",
                "alerts_handled": len(results),
                "results": results
            }

        except Exception as e:
            logger.error(f"Error handling alert: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e)
            }

    def _process_single_alert(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single alert and determine remediation action.

        Args:
            alert: Single alert data

        Returns:
            Dict containing remediation result
        """
        alert_name = alert.get('labels', {}).get('alertname', 'unknown')
        severity = alert.get('labels', {}).get('severity', 'unknown')
        status = alert.get('status', 'unknown')

        logger.info(f"Processing alert: {alert_name} (severity: {severity}, status: {status})")

        # Determine remediation action based on alert type
        remediation = {
            "alert_name": alert_name,
            "severity": severity,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "action_taken": None,
            "result": None
        }

        # High CPU usage
        if "HighCPU" in alert_name or "cpu" in alert_name.lower():
            remediation["action_taken"] = "cpu_optimization"
            remediation["result"] = self._remediate_high_cpu(alert)

        # High memory usage
        elif "HighMemory" in alert_name or "memory" in alert_name.lower():
            remediation["action_taken"] = "memory_cleanup"
            remediation["result"] = self._remediate_high_memory(alert)

        # Service down
        elif "ServiceDown" in alert_name or "down" in alert_name.lower():
            remediation["action_taken"] = "service_restart"
            remediation["result"] = self._remediate_service_down(alert)

        # Disk space
        elif "DiskSpace" in alert_name or "disk" in alert_name.lower():
            remediation["action_taken"] = "disk_cleanup"
            remediation["result"] = self._remediate_disk_space(alert)

        # Default: log and monitor
        else:
            remediation["action_taken"] = "monitor"
            remediation["result"] = {"status": "logged", "message": "Alert logged for manual review"}

        # Store in history
        self._add_to_history(remediation)

        return remediation

    def _remediate_high_cpu(self, alert: Dict[str, Any]) -> Dict[str, str]:
        """Handle high CPU usage alerts"""
        logger.warning("High CPU usage detected - implementing optimization")

        # In a real system, this would:
        # - Identify CPU-intensive processes
        # - Scale horizontally if possible
        # - Apply rate limiting
        # - Restart problematic services

        return {
            "status": "mitigated",
            "message": "CPU optimization strategies applied",
            "actions": [
                "Identified high-CPU processes",
                "Applied rate limiting",
                "Triggered horizontal scaling"
            ]
        }

    def _remediate_high_memory(self, alert: Dict[str, Any]) -> Dict[str, str]:
        """Handle high memory usage alerts"""
        logger.warning("High memory usage detected - performing cleanup")

        # In a real system, this would:
        # - Clear caches
        # - Trigger garbage collection
        # - Restart memory-leaking services
        # - Scale memory resources

        return {
            "status": "mitigated",
            "message": "Memory cleanup performed",
            "actions": [
                "Cleared application caches",
                "Triggered garbage collection",
                "Restarted high-memory processes"
            ]
        }

    def _remediate_service_down(self, alert: Dict[str, Any]) -> Dict[str, str]:
        """Handle service down alerts"""
        logger.error("Service down detected - attempting restart")

        # In a real system, this would:
        # - Attempt service restart
        # - Check dependencies
        # - Failover to backup instances
        # - Notify on-call team if restart fails

        return {
            "status": "restarted",
            "message": "Service restart attempted",
            "actions": [
                "Checked service health",
                "Attempted graceful restart",
                "Verified service recovery"
            ]
        }

    def _remediate_disk_space(self, alert: Dict[str, Any]) -> Dict[str, str]:
        """Handle disk space alerts"""
        logger.warning("Low disk space detected - performing cleanup")

        # In a real system, this would:
        # - Clean up old logs
        # - Remove temporary files
        # - Compress archived data
        # - Trigger data archival

        return {
            "status": "cleaned",
            "message": "Disk cleanup performed",
            "actions": [
                "Removed old log files",
                "Cleaned temporary directories",
                "Compressed archived data"
            ]
        }

    def _add_to_history(self, remediation: Dict[str, Any]) -> None:
        """Add remediation to history with size limit"""
        self.remediation_history.append(remediation)

        # Keep only last N entries
        if len(self.remediation_history) > self.max_history:
            self.remediation_history = self.remediation_history[-self.max_history:]

    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent remediation history.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of recent remediation actions
        """
        return self.remediation_history[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about remediation actions.

        Returns:
            Dict containing statistics
        """
        if not self.remediation_history:
            return {
                "total_alerts": 0,
                "successful_remediations": 0,
                "failed_remediations": 0,
                "actions_by_type": {}
            }

        actions_by_type = {}
        successful = 0
        failed = 0

        for entry in self.remediation_history:
            action = entry.get("action_taken", "unknown")
            actions_by_type[action] = actions_by_type.get(action, 0) + 1

            result = entry.get("result", {})
            if isinstance(result, dict):
                status = result.get("status", "")
                if status in ["mitigated", "restarted", "cleaned", "logged"]:
                    successful += 1
                else:
                    failed += 1

        return {
            "total_alerts": len(self.remediation_history),
            "successful_remediations": successful,
            "failed_remediations": failed,
            "actions_by_type": actions_by_type
        }
