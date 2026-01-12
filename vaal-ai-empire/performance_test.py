 feat/implement-authority-engine


# performance_test.py
 main
import time
import sys
import requests
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
 feat/implement-authority-engine
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


# A simple mock server to test against
class MockServerRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"OK")
        # Introduce a small delay to simulate network latency
        time.sleep(0.01)

def run_server(server_class=HTTPServer, handler_class=MockServerRequestHandler, port=8001):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()

# --- Functions to be benchmarked ---

def original_function(url, iterations):
    """Makes requests without a session."""
    for _ in range(iterations):
        try:
            requests.get(url, timeout=1)
        except requests.RequestException:
            pass # Ignore errors in test
    return "Original function complete"

def optimized_function(url, iterations):
    """Makes requests with a persistent session."""
    with requests.Session() as session:
        for _ in range(iterations):
            try:
                session.get(url, timeout=1)
            except requests.RequestException:
                pass # Ignore errors in test
    return "Optimized function complete"

def benchmark_function(func, url, iterations):
    """Benchmark a function over multiple iterations"""
    start = time.perf_counter()
    func(url, iterations)
    end = time.perf_counter()
    return end - start

def test_optimization():
    """Compare original vs optimized performance"""
    server_port = 8001
    server = HTTPServer(('', server_port), MockServerRequestHandler)
 main
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    # Give the server a moment to start
 feat/implement-authority-engine
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

    time.sleep(1)

    url = f"http://localhost:{server_port}"
    iterations = 50  # Number of requests to make

    print("=" * 60)
    print("PERFORMANCE COMPARISON: requests vs. requests.Session")
    print("=" * 60)
    print(f"Running {iterations} requests against a local mock server...")

    # Benchmark speed
    original_time = benchmark_function(original_function, url, iterations)
    optimized_time = benchmark_function(optimized_function, url, iterations)

    # Shutdown the server
    server.shutdown()
    server.server_close()

    # It's possible for the original time to be zero in very fast environments
    if original_time > 0:
        improvement = ((original_time - optimized_time) / original_time) * 100
    elif optimized_time == 0:
        improvement = 0 # No change
    else:
        improvement = -100  # Regression: optimized took time when original didn't

    print(f"\nOriginal (requests.get):  {original_time:.4f}s")
    print(f"Optimized (Session.get): {optimized_time:.4f}s")
    print("-" * 28)
    print(f"Improvement: {improvement:.1f}% faster")

    if improvement > 10:
        print("\n✅ SIGNIFICANT IMPROVEMENT: Connection pooling is effective.")
        return True
    elif improvement > 0:
        print("\n✅ Minor improvement detected.")
        return True
    else:
        print("\n⚠️ NO IMPROVEMENT - Optimization may not be effective in this environment.")
        return False

if __name__ == "__main__":
    print("Starting performance benchmark for HTTP request optimization...")
    success = test_optimization()
    print("=" * 60)
    if success:
        print("Benchmark PASSED")
    else:
        print("Benchmark FAILED: No performance improvement shown.")
    sys.exit(0 if success else 1)
 main
