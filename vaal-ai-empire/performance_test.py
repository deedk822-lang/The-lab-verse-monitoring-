# performance_test.py
import time
import sys
import requests
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

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
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    # Give the server a moment to start
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
