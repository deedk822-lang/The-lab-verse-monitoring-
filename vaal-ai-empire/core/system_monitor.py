"""
System Health Monitoring and Error Handling
Provides comprehensive monitoring, error tracking, and recovery mechanisms
"""

import logging
import time
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from functools import wraps
import os
import requests

logger = logging.getLogger(__name__)

class SystemMonitor:
    """Monitor system health and track errors"""

    def __init__(self, db=None):
        self.db = db
        self.session = requests.Session()
        self.start_time = datetime.now()
        self.error_count = 0
        self.warning_count = 0
        self.api_calls = {"success": 0, "failure": 0}

    def record_error(self, component: str, error: Exception,
                    context: Optional[Dict] = None):
        """Record an error for monitoring"""
        self.error_count += 1

        error_data = {
            "component": component,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.now().isoformat(),
            "context": context or {}
        }

        logger.error(f"[{component}] {type(error).__name__}: {error}")

        # Log to database if available
        if self.db:
            try:
                self.db.log_api_usage(
                    component,
                    "error",
                    success=False,
                    error_message=str(error)
                )
            except:
                pass  # Don't fail if logging fails

        return error_data

    def record_warning(self, component: str, message: str):
        """Record a warning"""
        self.warning_count += 1
        logger.warning(f"[{component}] {message}")

    def record_api_call(self, success: bool, provider: str,
                       operation: str, cost: float = 0.0):
        """Record API call statistics"""
        if success:
            self.api_calls["success"] += 1
        else:
            self.api_calls["failure"] += 1

        if self.db:
            try:
                self.db.log_api_usage(
                    provider,
                    operation,
                    cost_usd=cost,
                    success=success
                )
            except:
                pass

    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        uptime = (datetime.now() - self.start_time).total_seconds()

        status = {
            "uptime_seconds": uptime,
            "uptime_hours": uptime / 3600,
            "errors": self.error_count,
            "warnings": self.warning_count,
            "api_calls": self.api_calls,
            "success_rate": (
                self.api_calls["success"] /
                max(sum(self.api_calls.values()), 1)
            ) * 100,
            "timestamp": datetime.now().isoformat()
        }

        # Add database status
        if self.db:
            try:
                status["database"] = "healthy" if self.db.health_check() else "unhealthy"
            except:
                status["database"] = "error"

        # Add service health checks
        status["services"] = self.check_all_services()

        return status

    def check_all_services(self) -> Dict:
        """Check health of all external services"""
        services = {}

        # Check AI providers
        services["cohere"] = self._check_cohere()
        services["groq"] = self._check_groq()
        services["ollama"] = self._check_ollama()

        # Check communication services
        services["twilio"] = self._check_twilio()
        services["ayrshare"] = self._check_ayrshare()

        return services

    def _check_cohere(self) -> str:
        """Check Cohere API health"""
        try:
            from api.cohere import CohereAPI
            api = CohereAPI()
            # Simple test call
            result = api.generate_content("test", max_tokens=5)
            return "healthy"
        except ValueError:
            return "not_configured"
        except Exception as e:
            return f"error: {str(e)[:50]}"

    def _check_groq(self) -> str:
        """Check Groq API health"""
        try:
            from api.groq_api import GroqAPI
            api = GroqAPI()
            return "healthy"
        except ValueError:
            return "not_configured"
        except Exception as e:
            return f"error: {str(e)[:50]}"

    def _check_ollama(self) -> str:
        """Check Ollama server health"""
        try:
            response = self.session.get("http://localhost:11434", timeout=2)
            return "healthy" if response.status_code == 200 else "unreachable"
        except:
            return "not_running"

    def _check_twilio(self) -> str:
        """Check Twilio health"""
        try:
            from twilio.rest import Client
            sid = os.getenv("TWILIO_ACCOUNT_SID")
            token = os.getenv("TWILIO_AUTH_TOKEN")
            if not sid or not token:
                return "not_configured"
            # Don't actually call API, just check credentials exist
            return "configured"
        except ImportError:
            return "sdk_not_installed"
        except:
            return "error"

    def _check_ayrshare(self) -> str:
        """Check Ayrshare health"""
        api_key = os.getenv("AYRSHARE_API_KEY")
        if not api_key:
            return "not_configured"

        try:
            response = self.session.get(
                "https://app.ayrshare.com/api/profiles",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=5
            )
            return "healthy" if response.status_code == 200 else "error"
        except:
            return "unreachable"

    def generate_health_report(self) -> Dict:
        """Generate detailed health report"""
        status = self.get_system_status()

        report = {
            "summary": {
                "overall_health": self._calculate_health_score(status),
                "timestamp": datetime.now().isoformat(),
                "uptime_hours": round(status["uptime_hours"], 2)
            },
            "metrics": {
                "errors": status["errors"],
                "warnings": status["warnings"],
                "api_success_rate": round(status["success_rate"], 2)
            },
            "services": status["services"],
            "recommendations": self._generate_recommendations(status)
        }

        return report

    def _calculate_health_score(self, status: Dict) -> str:
        """Calculate overall health score"""
        healthy_services = sum(
            1 for s in status["services"].values()
            if s in ["healthy", "configured"]
        )
        total_services = len(status["services"])

        service_health = (healthy_services / total_services) * 100 if total_services > 0 else 0

        if service_health >= 80 and status["success_rate"] >= 90:
            return "excellent"
        elif service_health >= 60 and status["success_rate"] >= 75:
            return "good"
        elif service_health >= 40:
            return "degraded"
        else:
            return "critical"

    def _generate_recommendations(self, status: Dict) -> List[str]:
        """Generate recommendations based on status"""
        recommendations = []

        # Check services
        for service, health in status["services"].items():
            if health == "not_configured":
                recommendations.append(
                    f"Configure {service} by setting API keys in .env file"
                )
            elif health == "not_running":
                recommendations.append(
                    f"Start {service} service (e.g., ollama serve)"
                )
            elif "error" in health:
                recommendations.append(
                    f"Check {service} configuration - {health}"
                )

        # Check error rate
        if status["errors"] > 10:
            recommendations.append(
                "High error count detected. Review logs for recurring issues."
            )

        # Check success rate
        if status["success_rate"] < 80:
            recommendations.append(
                "Low API success rate. Check provider availability and quotas."
            )

        return recommendations


class ErrorHandler:
    """Decorator-based error handling and retry logic"""

    @staticmethod
    def with_retry(max_retries: int = 3, delay: float = 1.0,
                   backoff: float = 2.0, exceptions: tuple = (Exception,)):
        """
        Retry decorator with exponential backoff

        Usage:
            @ErrorHandler.with_retry(max_retries=3, delay=1.0)
            def my_function():
                # Your code here
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                current_delay = delay
                last_exception = None

                for attempt in range(max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e

                        if attempt < max_retries:
                            logger.warning(
                                f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}. "
                                f"Retrying in {current_delay}s..."
                            )
                            time.sleep(current_delay)
                            current_delay *= backoff
                        else:
                            logger.error(
                                f"All {max_retries + 1} attempts failed for {func.__name__}"
                            )

                raise last_exception

            return wrapper
        return decorator

    @staticmethod
    def with_fallback(fallback_func: Callable):
        """
        Execute fallback function if main function fails

        Usage:
            @ErrorHandler.with_fallback(fallback_function)
            def my_function():
                # Your code here
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.warning(
                        f"{func.__name__} failed: {e}. Executing fallback."
                    )
                    return fallback_func(*args, **kwargs)

            return wrapper
        return decorator

    @staticmethod
    def log_execution(log_level: str = "INFO"):
        """
        Log function execution time and result

        Usage:
            @ErrorHandler.log_execution(log_level="INFO")
            def my_function():
                # Your code here
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                start_time = time.time()
                func_name = func.__name__

                logger.log(
                    getattr(logging, log_level),
                    f"Starting {func_name}"
                )

                try:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time

                    logger.log(
                        getattr(logging, log_level),
                        f"Completed {func_name} in {execution_time:.2f}s"
                    )

                    return result

                except Exception as e:
                    execution_time = time.time() - start_time
                    logger.error(
                        f"Failed {func_name} after {execution_time:.2f}s: {e}"
                    )
                    raise

            return wrapper
        return decorator

    @staticmethod
    def safe_execute(func: Callable, *args, default_return: Any = None,
                    log_errors: bool = True, **kwargs) -> Any:
        """
        Safely execute a function, returning default value on error

        Usage:
            result = ErrorHandler.safe_execute(
                risky_function,
                arg1, arg2,
                default_return={},
                kwarg1=value1
            )
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if log_errors:
                logger.error(f"Error in {func.__name__}: {e}")
                logger.debug(traceback.format_exc())
            return default_return


class AlertSystem:
    """Send alerts when critical issues occur"""

    def __init__(self, db=None, webhook_url: Optional[str] = None, session=None):
        self.db = db
        self.webhook_url = webhook_url or os.getenv("ALERT_WEBHOOK_URL")
        self.session = session or requests.Session()
        self.alert_history = []

    def send_alert(self, severity: str, component: str,
                   message: str, details: Optional[Dict] = None):
        """
        Send alert via configured channels

        Args:
            severity: "info", "warning", "error", "critical"
            component: Component that generated alert
            message: Alert message
            details: Additional context
        """
        alert = {
            "timestamp": datetime.now().isoformat(),
            "severity": severity,
            "component": component,
            "message": message,
            "details": details or {}
        }

        self.alert_history.append(alert)

        # Log alert
        log_func = getattr(logger, severity.lower(), logger.info)
        log_func(f"[ALERT] [{component}] {message}")

        # Send to webhook if configured
        if self.webhook_url and severity in ["error", "critical"]:
            self._send_webhook(alert)

        # Store in database
        if self.db:
            try:
                self.db.log_api_usage(
                    f"alert_{component}",
                    severity,
                    success=False,
                    error_message=message
                )
            except:
                pass

    def _send_webhook(self, alert: Dict):
        """Send alert to webhook (Slack, Discord, etc.)"""
        try:
            payload = {
                "text": f"🚨 {alert['severity'].upper()}: {alert['message']}",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*{alert['component']}*\n{alert['message']}"
                        }
                    }
                ]
            }

            self.session.post(self.webhook_url, json=payload, timeout=5)
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")

    def get_recent_alerts(self, count: int = 10,
                         severity: Optional[str] = None) -> List[Dict]:
        """Get recent alerts, optionally filtered by severity"""
        alerts = self.alert_history[-count:]

        if severity:
            alerts = [a for a in alerts if a["severity"] == severity]

        return alerts


# Global instances
_monitor = None
_alert_system = None

def get_monitor(db=None) -> SystemMonitor:
    """Get global monitor instance"""
    global _monitor
    if _monitor is None:
        _monitor = SystemMonitor(db)
    return _monitor

def get_alert_system(db=None) -> AlertSystem:
    """Get global alert system instance"""
    global _alert_system
    if _alert_system is None:
        monitor = get_monitor(db)
        _alert_system = AlertSystem(db, session=monitor.session)
    return _alert_system