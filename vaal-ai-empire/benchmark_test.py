import time
import requests
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import sys

# --- Test HTTP Server Setup ---
class QuietHTTPRequestHandler(BaseHTTPRequestHandler):
    """A simple handler that returns 200 OK and suppresses log messages."""
    def do_POST(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'{"status": "ok"}')

    def log_message(self, format, *args):
        """Suppress logging to keep benchmark output clean."""
        pass

def run_server(server_class=HTTPServer, handler_class=QuietHTTPRequestHandler, port=8000):
    """Runs the HTTP server in a separate thread."""
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()

# --- Benchmark Functions ---

def benchmark_without_session(api_url, iterations=20):
    """Makes N requests without connection pooling."""
    start_time = time.perf_counter()
    for _ in range(iterations):
        requests.post(api_url, json={"inputs": "test"}, timeout=5)
    end_time = time.perf_counter()
    return end_time - start_time

def benchmark_with_session(api_url, iterations=20):
    """Makes N requests WITH connection pooling."""
    session = requests.Session()
    start_time = time.perf_counter()
    for _ in range(iterations):
        session.post(api_url, json={"inputs": "test"}, timeout=5)
    end_time = time.perf_counter()
    session.close()
    return end_time - start_time

def test_optimization():
    """
    Main function to run the benchmark.
    1. Starts a local HTTP server.
    2. Runs benchmarks against it.
    3. Compares results and prints the improvement.
    """
    PORT = 8080
    SERVER_URL = f"http://localhost:{PORT}/"
    ITERATIONS = 20

    # Start the server in a daemon thread
    server_thread = threading.Thread(target=run_server, kwargs={'port': PORT})
    server_thread.daemon = True
    server_thread.start()
    time.sleep(0.5)

    print("=" * 60)
    print("⚡ Bolt: Connection Reuse Performance Benchmark ⚡")
    print("=" * 60)
    print(f"Running {ITERATIONS} requests against a local server...")

    original_time = benchmark_without_session(SERVER_URL, ITERATIONS)
    print(f"\nOriginal (requests.post):      {original_time:.4f}s")

    optimized_time = benchmark_with_session(SERVER_URL, ITERATIONS)
    print(f"Optimized (session.post):      {optimized_time:.4f}s")

    if original_time > 0 and optimized_time < original_time:
        improvement = ((original_time - optimized_time) / original_time) * 100
        print("\n" + "="*60)
        print(f"✅ SUCCESS: Connection reuse is {improvement:.1f}% faster.")
        print("="*60)
        return True
    else:
        print("\n" + "="*60)
        print("⚠️  WARNING: No significant performance improvement detected.")
        print("="*60)
        return False


if __name__ == "__main__":
    success = test_optimization()
    sys.exit(0 if success else 1)
