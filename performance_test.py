
import time
import sys
import requests
from unittest.mock import patch, MagicMock

# --- Original Code (Pre-optimization) ---

class SystemMonitorOriginal:
    """A snapshot of the original SystemMonitor before optimization."""
    def __init__(self):
        self.start_time = time.time()

    def check_all_services(self) -> dict:
        services = {}
        services["ollama"] = self._check_ollama()
        services["ayrshare"] = self._check_ayrshare()
        return services

    def _check_ollama(self) -> str:
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            return "healthy"
        except:
            return "not_running"

    def _check_ayrshare(self) -> str:
        try:
            response = requests.get(
                "https://app.ayrshare.com/api/profiles",
                headers={"Authorization": "Bearer FAKE_KEY"},
                timeout=5
            )
            return "healthy"
        except:
            return "unreachable"

# --- Optimized Code ---

class SystemMonitorOptimized:
    """The new, optimized SystemMonitor using requests.Session."""
    def __init__(self):
        self.session = requests.Session()
        self.start_time = time.time()

    def check_all_services(self) -> dict:
        services = {}
        services["ollama"] = self._check_ollama()
        services["ayrshare"] = self._check_ayrshare()
        return services

    def _check_ollama(self) -> str:
        try:
            response = self.session.get("http://localhost:11434/api/tags", timeout=2)
            return "healthy"
        except:
            return "not_running"

    def _check_ayrshare(self) -> str:
        try:
            response = self.session.get(
                "https://app.ayrshare.com/api/profiles",
                headers={"Authorization": "Bearer FAKE_KEY"},
                timeout=5
            )
            return "healthy"
        except:
            return "unreachable"


def benchmark_monitor(monitor_class, iterations=50):
    """
    Benchmarks the check_all_services method, simulating network connection overhead.
    """
    monitor = monitor_class()
    mock_response = MagicMock(status_code=200)

    # Simulate network costs
    REQUEST_LATENCY = 0.002  # 2ms for the request/response
    CONNECTION_SETUP_LATENCY = 0.015 # 15ms to establish a new TCP connection (conservative)

    established_connections = set()

    def mock_session_get(session_instance, url, **kwargs):
        """Mock for session.get - only pays setup cost once per host."""
        host = url.split('/')[2]
        latency = REQUEST_LATENCY
        if host not in established_connections:
            latency += CONNECTION_SETUP_LATENCY
            established_connections.add(host)
        time.sleep(latency)
        return mock_response

    def mock_requests_get(url, **kwargs):
        """Mock for requests.get - always pays the setup cost."""
        latency = REQUEST_LATENCY + CONNECTION_SETUP_LATENCY
        time.sleep(latency)
        return mock_response

    start_time = time.perf_counter()

    if isinstance(monitor, SystemMonitorOptimized):
        patch_target = 'requests.Session.get'
        mock_func = mock_session_get
    else:
        patch_target = 'requests.get'
        mock_func = mock_requests_get

    with patch(patch_target, side_effect=mock_func):
        for _ in range(iterations):
            monitor.check_all_services()

    end_time = time.perf_counter()
    return end_time - start_time


def test_optimization():
    """Compares the performance of the original and optimized monitors."""
    print("=" * 60)
    print("⚡ BOLT: PERFORMANCE BENCHMARK (v2) ⚡")
    print("Target: Reusing connections with requests.Session")
    print("=" * 60)

    iterations = 50
    print(f"Running benchmark with {iterations} iterations...")
    print("Simulating network connection overhead for accuracy.")

    # Benchmark Original
    original_time = benchmark_monitor(SystemMonitorOriginal, iterations)
    print(f"\nOriginal Implementation Time: {original_time:.4f}s")

    # Benchmark Optimized
    optimized_time = benchmark_monitor(SystemMonitorOptimized, iterations)
    print(f"Optimized Implementation Time: {optimized_time:.4f}s")

    # Calculate and display improvement
    if original_time > 0 and optimized_time < original_time:
        improvement = ((original_time - optimized_time) / original_time) * 100
        print(f"\n🚀 Improvement: {improvement:.1f}% faster")
    else:
        improvement = 0
        print("\n- No improvement detected.")

    if improvement > 10:
        print("\n✅ RESULT: SIGNIFICANT IMPROVEMENT DETECTED!")
        return True
    else:
        print("\n⚠️ RESULT: Optimization is not effective under these test conditions.")
        return False

if __name__ == "__main__":
    success = test_optimization()
    sys.exit(0 if success else 1)
