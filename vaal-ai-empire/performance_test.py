
import time
import os
import threading
import sys
import requests
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- Bootstrap to handle package name with hyphens ---
# This script is run from the repo root.
original_dir_name = 'vaal-ai-empire'
valid_package_name = 'vaal_ai_empire'
renamed_for_import = False
if os.path.exists(original_dir_name):
    os.rename(original_dir_name, valid_package_name)
    renamed_for_import = True

# We can now import the module since the package name is valid.
# The CWD is the repo root, so we add it to the path.
sys.path.insert(0, '.')

try:
    from vaal_ai_empire.api.huggingface_api import HuggingFaceAPI

    # --- Mock server to simulate the Hugging Face API endpoint ---
    class MockServerRequestHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')

        def log_message(self, format, *args):
            # Silence the server logs for clean test output
            return

    # --- Unoptimized HuggingFaceAPI for comparison ---
    class UnoptimizedHuggingFaceAPI(HuggingFaceAPI):
        """A version of the client that *doesn't* use session pooling for the status check."""
        def check_model_status(self, model: str):
            api_url = f"{self.api_base}/{model}"
            try:
                # This is the unoptimized part: using requests directly
                response = requests.post(
                    api_url,
                    headers=self.headers,
                    json={"inputs": "test"},
                    timeout=5
                )
                return {
                    "model": model,
                    "status": "ready" if response.status_code == 200 else "loading",
                    "status_code": response.status_code
                }
            except Exception as e:
                return {"model": model, "status": "error", "error": str(e)}

    def benchmark(api_client, iterations=50):
        """Benchmarks the check_model_status method of a given API client."""
        start_time = time.perf_counter()
        for _ in range(iterations):
            api_client.check_model_status("test-model")
        end_time = time.perf_counter()
        return end_time - start_time

    def main():
        """Main function to run the benchmark and report results."""
        os.environ["HUGGINGFACE_TOKEN"] = "test-token"

        server_port = 8000
        httpd = HTTPServer(('', server_port), MockServerRequestHandler)
        server_thread = threading.Thread(target=httpd.serve_forever)
        server_thread.daemon = True
        server_thread.start()

        try:
            unoptimized_client = UnoptimizedHuggingFaceAPI()
            unoptimized_client.api_base = f"http://localhost:{server_port}"

            optimized_client = HuggingFaceAPI()
            optimized_client.api_base = f"http://localhost:{server_port}"

            iterations = 50
            print("=" * 60)
            print("⚡️ Bolt Performance Benchmark: HuggingFace API Connection Reuse")
            print("=" * 60)
            print(f"Running {iterations} status checks to compare performance...")

            unoptimized_time = benchmark(unoptimized_client, iterations)
            optimized_time = benchmark(optimized_client, iterations)

            improvement = ((unoptimized_time - optimized_time) / unoptimized_time) * 100

            print(f"\nOriginal (requests.post):  {unoptimized_time:.4f}s")
            print(f"Optimized (session.post):  {optimized_time:.4f}s")
            print("-" * 60)

            if improvement > 10: # TCP handshake overhead is significant
                print(f"✅ PASSED: Optimization is {improvement:.1f}% faster.")
                return True
            else:
                print(f"❌ FAILED: No significant performance improvement detected ({improvement:.1f}%).")
                return False
        finally:
            httpd.shutdown()
            httpd.server_close()
            server_thread.join()

    # --- Execute the benchmark ---
    success = main()
    sys.exit(0 if success else 1)

finally:
    # --- Cleanup: Restore original directory name ---
    if renamed_for_import and os.path.exists(valid_package_name):
        os.rename(valid_package_name, original_dir_name)
