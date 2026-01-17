
import time
import os
import sys
import threading
import requests
from http.server import BaseHTTPRequestHandler, HTTPServer
import unittest
from unittest.mock import patch

import importlib

# Add the project root to the Python path to allow for clean imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Dynamically import the HuggingFaceAPI module
huggingface_api_module = importlib.import_module("vaal-ai-empire.api.huggingface_api")
HuggingFaceAPI = huggingface_api_module.HuggingFaceAPI

# Mock server to simulate the Hugging Face API
class MockAPIHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"status": "ok"}')

def run_server(server_class=HTTPServer, handler_class=MockAPIHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()

class TestHuggingFaceAPIPerformance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Start the mock server in a separate thread
        cls.server = HTTPServer(('', 8000), MockAPIHandler)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever)
        cls.server_thread.daemon = True
        cls.server_thread.start()
        time.sleep(1)  # Give the server a moment to start

    @classmethod
    def tearDownClass(cls):
        # Shut down the server
        cls.server.shutdown()
        cls.server.server_close()
        cls.server_thread.join()

    @patch.dict(os.environ, {"HUGGINGFACE_TOKEN": "test-token"})
    def test_connection_reuse_performance(self):
        """
        Benchmark the performance difference between using a new connection
        for each request versus reusing a connection with a session object.
        """
        iterations = 10
        model = "distilbert-base-uncased"

        # --- Benchmark 1: Original implementation (without session) ---
        # We simulate the old behavior by calling requests.post directly
        time_no_session = 0
        headers = {"Authorization": "Bearer test-token"}
        api_url = f"http://localhost:8000/{model}"

        start_time = time.perf_counter()
        for _ in range(iterations):
            requests.post(api_url, headers=headers, json={"inputs": "test"})
        end_time = time.perf_counter()
        time_no_session = end_time - start_time

        # --- Benchmark 2: Optimized implementation (with session) ---
        # The optimized code uses the session object from the HuggingFaceAPI class
        api_client = HuggingFaceAPI()
        # Point the client to the local mock server
        api_client.api_base = "http://localhost:8000"

        start_time = time.perf_counter()
        for _ in range(iterations):
            api_client.check_model_status(model)
        end_time = time.perf_counter()
        time_with_session = end_time - start_time
        api_client.close()

        print("\n" + "="*60)
        print("PERFORMANCE COMPARISON: CONNECTION REUSE")
        print("="*60)
        print(f"Time without session ({iterations} requests): {time_no_session:.4f}s")
        print(f"Time with session ({iterations} requests):    {time_with_session:.4f}s")

        self.assertLess(time_with_session, time_no_session,
                        "The session-based approach should be faster than creating new connections.")

        if time_no_session > 0:
            improvement = ((time_no_session - time_with_session) / time_no_session) * 100
            print(f"Improvement: {improvement:.2f}% faster")
            self.assertGreater(improvement, 10, "Expected a significant performance improvement of at least 10%.")

if __name__ == "__main__":
    unittest.main()
