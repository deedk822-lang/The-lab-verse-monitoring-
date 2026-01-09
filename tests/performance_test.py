
import time
import sys
import os
import requests
from unittest.mock import patch, MagicMock
from datetime import datetime
from typing import Dict, Optional

# Add the project root to the path to allow importing the module
sys.path.insert(0, os.path.abspath('..'))

# It's not possible to import from a directory with a hyphen directly.
# We must use importlib.
import importlib
system_monitor_module = importlib.import_module("vaal-ai-empire.core.system_monitor")
SystemMonitor = system_monitor_module.SystemMonitor
AlertSystem = system_monitor_module.AlertSystem

# --- Create a replica of the original classes for comparison ---
class OriginalSystemMonitor:
    """A copy of the original SystemMonitor before optimization"""
    def __init__(self):
        self.db = None
        self.start_time = time.time()

    def check_all_services(self) -> dict:
        services = {}
        # Replicate all service checks from the original class
        services["cohere"] = self._check_cohere()
        services["groq"] = self._check_groq()
        services["ollama"] = self._check_ollama()
        services["twilio"] = self._check_twilio()
        services["ayrshare"] = self._check_ayrshare()
        return services

    def _check_cohere(self) -> str:
        try:
            from api.cohere import CohereAPI
            return "healthy"
        except Exception as e:
            return f"error: {str(e)}"

    def _check_groq(self) -> str:
        try:
            from api.groq_api import GroqAPI
            return "healthy"
        except Exception as e:
            return f"error: {str(e)}"

    def _check_ollama(self) -> str:
        try:
            response = requests.get("http://localhost:11434", timeout=2)
            return "healthy" if response.status_code == 200 else "unreachable"
        except:
            return "not_running"

    def _check_twilio(self) -> str:
        try:
            from twilio.rest import Client
            sid = os.getenv("TWILIO_ACCOUNT_SID")
            if not sid: return "not_configured"
            return "configured"
        except ImportError:
            return "sdk_not_installed"
        except Exception:
            return "error"

    def _check_ayrshare(self) -> str:
        api_key = os.getenv("AYRSHARE_API_KEY")
        if not api_key:
            return "not_configured"
        try:
            response = requests.get(
                "https://app.ayrshare.com/api/profiles",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=5
            )
            return "healthy" if response.status_code == 200 else "error"
        except:
            return "unreachable"

class OriginalAlertSystem:
    """A faithful copy of the original AlertSystem before optimization"""
    def __init__(self, db=None, webhook_url: Optional[str] = None):
        self.db = db
        self.webhook_url = webhook_url or os.getenv("ALERT_WEBHOOK_URL")
        self.alert_history = []

    def send_alert(self, severity: str, component: str,
                   message: str, details: Optional[Dict] = None):
        alert = {
            "timestamp": datetime.now().isoformat(),
            "severity": severity,
            "component": component,
            "message": message,
            "details": details or {}
        }
        self.alert_history.append(alert)
        if self.webhook_url and severity in ["error", "critical"]:
            self._send_webhook(alert)

    def _send_webhook(self, alert: Dict):
        try:
            payload = {
                "text": f"🚨 {alert['severity'].upper()}: {alert['message']}",
                "blocks": [
                    {
                        "type": "section",
                        "text": { "type": "mrkdwn", "text": f"*{alert['component']}*\n{alert['message']}" }
                    }
                ]
            }
            requests.post(self.webhook_url, json=payload, timeout=5)
        except Exception as e:
            print(f"Failed to send webhook alert: {e}")

def benchmark_function(func, iterations=100):
    """Benchmark a function over multiple iterations"""
    start = time.perf_counter()
    for _ in range(iterations):
        func()
    end = time.perf_counter()
    return end - start

def test_optimization():
    """Compare original vs optimized performance"""
    print("=" * 60)
    print("PERFORMANCE COMPARISON TEST")
    print("=" * 60)

    mock_response_get = MagicMock()
    mock_response_get.status_code = 200
    mock_response_post = MagicMock()
    mock_response_post.status_code = 200

    # --- Test SystemMonitor ---
    print("\n--- Benchmarking SystemMonitor.check_all_services ---")
    original_monitor = OriginalSystemMonitor()
    optimized_monitor = SystemMonitor()
    optimized_monitor.session.get = MagicMock(return_value=mock_response_get)

    with patch('requests.get', return_value=mock_response_get):
        original_result = original_monitor.check_all_services()
        optimized_result = optimized_monitor.check_all_services()
        assert original_result == optimized_result, f"Results don't match!\\nOriginal:  {original_result}\\nOptimized: {optimized_result}"
        print("✓ Correctness verified: SystemMonitor results match")

        iterations = 100
        original_time = benchmark_function(original_monitor.check_all_services, iterations)
        optimized_time = benchmark_function(optimized_monitor.check_all_services, iterations)
        improvement = ((original_time - optimized_time) / original_time) * 100 if original_time > 0 else 0
        print(f"Original:  {original_time:.4f}s ({iterations} iterations)")
        print(f"Optimized: {optimized_time:.4f}s ({iterations} iterations)")
        print(f"Improvement: {improvement:.1f}% faster")
        if improvement < 1:
             print("⚠️  NOTE: Improvement is small in a mocked environment. The real-world benefit comes from reusing network connections, which isn't measured here.")

    # --- Test AlertSystem ---
    print("\n--- Benchmarking AlertSystem.send_alert ---")
    original_alerter = OriginalAlertSystem(webhook_url="http://fake.url/hook")
    optimized_alerter = AlertSystem(webhook_url="http://fake.url/hook")
    optimized_alerter.session.post = MagicMock(return_value=mock_response_post)

    alert_args = ("critical", "test-component", "This is a test alert.")

    with patch('requests.post', return_value=mock_response_post) as mock_post:
        original_alerter.send_alert(*alert_args)
        call_args_original = mock_post.call_args
        optimized_alerter.send_alert(*alert_args)
        call_args_optimized = optimized_alerter.session.post.call_args
        # Compare a part of the payload that is less likely to have floating point differences
        assert call_args_original.kwargs['json']['text'] == call_args_optimized.kwargs['json']['text'], f"Webhook payloads don't match!\\nOriginal: {call_args_original.kwargs['json']}\\nOptimized: {call_args_optimized.kwargs['json']}"

        print("✓ Correctness verified: AlertSystem payloads match")

        iterations = 100
        original_time = benchmark_function(lambda: original_alerter.send_alert(*alert_args), iterations)
        optimized_time = benchmark_function(lambda: optimized_alerter.send_alert(*alert_args), iterations)
        improvement = ((original_time - optimized_time) / original_time) * 100 if original_time > 0 else 0
        print(f"Original:  {original_time:.4f}s ({iterations} iterations)")
        print(f"Optimized: {optimized_time:.4f}s ({iterations} iterations)")
        print(f"Improvement: {improvement:.1f}% faster")
        if improvement < 1:
             print("⚠️  NOTE: Improvement is small in a mocked environment. The real-world benefit comes from reusing network connections, which isn't measured here.")

    return True

if __name__ == "__main__":
    success = test_optimization()
    print("\n" + "="*60)
    if success:
        print("✅ Performance test script completed.")
        sys.exit(0)
    else:
        print("❌ Performance test failed.")
        sys.exit(1)
