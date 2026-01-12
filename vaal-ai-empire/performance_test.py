
import time
import sys
import requests
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import socketserver

# A multi-threaded server is crucial for benchmarking connection pooling
class ThreadingHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    pass

class MockHandler(BaseHTTPRequestHandler):
    """A simple handler that returns 200 OK to any request."""
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')

    def log_message(self, format, *args):
        # Silence the server logs for clean test output
        return

class SystemMonitorOriginal:
    """A recreation of the original SystemMonitor's HTTP request logic."""
    def _check_ollama(self) -> str:
        try:
            # The original implementation creates a new connection for each call
            response = requests.get("http://localhost:11434", timeout=2)
            return "healthy" if response.status_code == 200 else "unreachable"
        except requests.exceptions.RequestException:
            return "not_running"

# Import the optimized class from the modified file
from core.system_monitor import SystemMonitor

def benchmark_function(func, iterations=100):
    """Benchmark a function over multiple iterations"""
    start = time.perf_counter()
    for _ in range(iterations):
        func()
    end = time.perf_counter()
    return end - start

def run_performance_test():
    """Compare original vs optimized performance and correctness."""
    # Start mock server in a background thread
    server = ThreadingHTTPServer(('localhost', 11434), MockHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    # Give the server a moment to start
    time.sleep(0.1)

    print("=" * 60)
    print("⚡ BOLT: PERFORMANCE BENCHMARK ⚡")
    print("=" * 60)
    print("Target: HTTP Connection Pooling with requests.Session")
    print("-" * 60)

    # Instantiate both versions
    original_monitor = SystemMonitorOriginal()
    optimized_monitor = SystemMonitor()

    # 1. Verify Correctness
    print("1. Verifying correctness...")
    original_result = original_monitor._check_ollama()
    optimized_result = optimized_monitor._check_ollama()

    if original_result != "healthy" or optimized_result != "healthy":
        print(f"  - ❌ FAILED: Health checks did not return 'healthy'.")
        print(f"    Original: {original_result}, Optimized: {optimized_result}")
        server.shutdown()
        return False

    print(f"  - ✅ PASSED: Both methods returned '{optimized_result}'.")

    # 2. Run Benchmark
    iterations = 50
    print(f"\n2. Running speed benchmark ({iterations} iterations)...")

    original_time = benchmark_function(original_monitor._check_ollama, iterations)
    optimized_time = benchmark_function(optimized_monitor._check_ollama, iterations)

    print(f"  - Original Implementation:  {original_time:.4f}s")
    print(f"  - Optimized Implementation: {optimized_time:.4f}s")

    # 3. Analyze Results
    print("\n3. Analyzing results...")
    if optimized_time >= original_time:
        improvement = 0
        print("  - ⚠️ WARNING: Optimization showed no improvement or was slower.")
    else:
        improvement = ((original_time - optimized_time) / original_time) * 100
        print(f"  - 🚀 IMPROVEMENT: {improvement:.2f}% faster")

    # Stop the server
    server.shutdown()

    print("=" * 60)

    # The test is successful if there is a measurable improvement
    return improvement > 10

if __name__ == "__main__":
    success = run_performance_test()
    if success:
        print("✅ Benchmark successful: Significant performance improvement verified.")
        sys.exit(0)
    else:
        print("❌ Benchmark failed: No significant performance improvement.")
        sys.exit(1)
