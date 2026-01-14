 feat/implement-authority-engine
 feat/implement-authority-engine


# performance_test.py
 main

# vaal-ai-empire/performance_test.py
 main
import time
import sys
import os
import requests
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
 feat/implement-authority-engine
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


import json
 main

# Set a dummy token for initialization
os.environ['HUGGINGFACE_TOKEN'] = 'test-token'

# --- Local Mock Server ---
class MockAPIHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = [{"generated_text": "mocked response"}]
        self.wfile.write(json.dumps(response).encode('utf-8'))

def run_server(server_class=HTTPServer, handler_class=MockAPIHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()

# --- Code to Benchmark ---

# Original (No Session)
class OriginalHuggingFaceAPI:
    def __init__(self, api_base="http://localhost:8000"):
        self.api_token = os.getenv("HUGGINGFACE_TOKEN")
        self.api_base = api_base
        self.headers = {"Authorization": f"Bearer {self.api_token}"}
        self.default_model = "test-model"

    def generate(self, prompt: str):
        api_url = f"{self.api_base}/{self.default_model}"
        payload = {"inputs": prompt}
        response = requests.post(api_url, headers=self.headers, json=payload)
        return response.json()

# Optimized (With Session)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from api.huggingface_api import HuggingFaceAPI as OptimizedHuggingFaceAPI


def benchmark(api_client, iterations=50):
    """Benchmark an API client by making real local requests."""
    start = time.perf_counter()
    for i in range(iterations):
        try:
            api_client.generate(f"test prompt {i}")
        except Exception as e:
            print(f"An error occurred: {e}")
            # In a real scenario, you might want to handle this more gracefully
            pass
    end = time.perf_counter()
    return end - start

 feat/implement-authority-engine
def test_optimization():
    """Compare original vs optimized performance"""
    server_port = 8001
    server = HTTPServer(('', server_port), MockServerRequestHandler)
 main

def main():
    """Main function to run the benchmark."""
    port = 8000
    server = HTTPServer(('', port), MockAPIHandler)
 main
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

 feat/implement-authority-engine
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

    time.sleep(1) # Give the server a moment to start
 main

    print("=" * 60)
    print("PERFORMANCE BENCHMARK: requests vs. requests.Session")
    print("=" * 60)
    print("Running a real local server to measure connection overhead.")
    print("-" * 60)

    iterations = 50

    # Benchmark Original
    print(f"Benchmarking Original API ({iterations} requests)...")
    original_api = OriginalHuggingFaceAPI(api_base=f"http://localhost:{port}")
    original_time = benchmark(original_api, iterations)

    # Benchmark Optimized
    print(f"Benchmarking Optimized API ({iterations} requests)...")
    with OptimizedHuggingFaceAPI() as optimized_api:
        # We need to manually override the api_base for the test
        optimized_api.api_base = f"http://localhost:{port}"
        optimized_time = benchmark(optimized_api, iterations)

    server.shutdown()
    server.server_close()

    print("\n" + "=" * 60)
    print("BENCHMARK RESULTS")
    print("=" * 60)
    print(f"Original API (new connection per request):  {original_time:.4f}s")
    print(f"Optimized API (reusing connections):      {optimized_time:.4f}s")
    print("-" * 60)

    if original_time > optimized_time:
        improvement = ((original_time - optimized_time) / original_time) * 100
        print(f"Improvement: {improvement:.1f}% faster")
        print("\n✅ SUCCESS: requests.Session is measurably faster.")
        success = True
    else:
        print("\n⚠️ WARNING: No performance improvement was measured.")
        success = False

    # Clean up the env var
    del os.environ['HUGGINGFACE_TOKEN']

    sys.exit(0 if success else 1)
 feat/implement-authority-engine
 main


if __name__ == "__main__":
    main()
 main
