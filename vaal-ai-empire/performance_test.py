# vaal-ai-empire/performance_test.py
import time
import sys
import os
import requests
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

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

def main():
    """Main function to run the benchmark."""
    port = 8000
    server = HTTPServer(('', port), MockAPIHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    time.sleep(1) # Give the server a moment to start

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

if __name__ == "__main__":
    main()
