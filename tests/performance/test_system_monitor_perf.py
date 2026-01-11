
import time
import sys
import os
import requests
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

# --- A simple HTTP server to field requests ---
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    """A basic handler that introduces a small delay to simulate network latency."""
    def do_GET(self):
        time.sleep(0.01)  # 10ms simulated network latency
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')

    def log_message(self, format, *args):
        # Suppress log messages for a cleaner benchmark output
        return

def run_server(server_class=ThreadingHTTPServer, handler_class=SimpleHTTPRequestHandler, port=8000):
    """Run the HTTP server in a separate thread."""
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()

# --- Test Subjects: Clean, simple classes for a clear A/B test ---

class MonitorWithoutSession:
    """Makes HTTP requests using the top-level `requests` library."""
    def check_services(self, url, num_requests=20):
        try:
            for _ in range(num_requests):
                requests.get(url, timeout=1)
        except requests.exceptions.RequestException:
            pass

class MonitorWithSession:
    """Makes HTTP requests using a `requests.Session` object for connection pooling."""
    def __init__(self):
        self.session = requests.Session()

    def check_services(self, url, num_requests=20):
        try:
            for _ in range(num_requests):
                self.session.get(url, timeout=1)
        except requests.exceptions.RequestException:
            pass

# --- Benchmark Execution ---

def benchmark_monitor(monitor, url, iterations=10, num_requests_per_iter=20):
    """Generic benchmark function."""
    start_time = time.perf_counter()
    for _ in range(iterations):
        monitor.check_services(url, num_requests=num_requests_per_iter)
    end_time = time.perf_counter()
    return end_time - start_time

def test_optimization():
    """Compare performance of the two monitoring classes."""
    SERVER_PORT = 8002
    SERVER_URL = f"http://localhost:{SERVER_PORT}"

    # Start the local server in a background thread
    server = ThreadingHTTPServer(('', SERVER_PORT), SimpleHTTPRequestHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(0.5)  # Wait for the server to be ready

    print("=" * 60)
    print("PERFORMANCE COMPARISON: requests vs. requests.Session")
    print("=" * 60)

    iterations = 10
    num_requests = 20
    total_requests = iterations * num_requests

    # --- Benchmark Original (No Session) ---
    monitor_no_session = MonitorWithoutSession()
    original_time = benchmark_monitor(monitor_no_session, SERVER_URL, iterations, num_requests)

    # --- Benchmark Optimized (With Session) ---
    monitor_with_session = MonitorWithSession()
    optimized_time = benchmark_monitor(monitor_with_session, SERVER_URL, iterations, num_requests)

    # Stop the server
    server.shutdown()
    server.server_close()
    server_thread.join()

    # --- Results ---
    improvement = ((original_time - optimized_time) / original_time) * 100 if original_time > 0 else 0

    print(f"Original (requests):   {original_time:.4f}s ({total_requests} total requests)")
    print(f"Optimized (Session):  {optimized_time:.4f}s ({total_requests} total requests)")
    print(f"Improvement: {improvement:.1f}% faster")

    if improvement > 20: # Expecting a significant improvement with latency
        print("\n✓ SIGNIFICANT IMPROVEMENT - Connection pooling is working effectively.")
        success = True
    else:
        print("\n⚠️ NO IMPROVEMENT DETECTED - The optimization is not effective.")
        success = False

    return success

if __name__ == "__main__":
    is_successful = test_optimization()
    sys.exit(0 if is_successful else 1)
