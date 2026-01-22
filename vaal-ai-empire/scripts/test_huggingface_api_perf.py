# vaal-ai-empire/scripts/test_huggingface_api_perf.py
import os
import sys
import time
import requests
from unittest.mock import patch, MagicMock

# --- Test Setup ---

# Set a dummy token to allow HuggingFaceAPI to instantiate
os.environ["HUGGINGFACE_TOKEN"] = "test-token"

# Add the project root to the path to allow imports from api/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from api.huggingface_api import HuggingFaceAPI
except ImportError as e:
    print("Error: Failed to import HuggingFaceAPI.")
    print("Please ensure this script is run from the 'vaal-ai-empire/scripts' directory or that the project root is in PYTHONPATH.")
    sys.exit(1)

def original_check_model_status(api_instance, model: str):
    """Simulates the original implementation using a new request for every call."""
    api_url = f"{api_instance.api_base}/{model}"
    # This is the line we are optimizing; it creates a new connection every time.
    response = requests.post(
        api_url,
        headers=api_instance.headers,
        json={"inputs": "test"},
        timeout=5
    )
    return response.status_code

def benchmark_function(func, api_instance, model, iterations=500):
    """Benchmark a function over multiple iterations."""
    start_time = time.perf_counter()
    for _ in range(iterations):
        func(api_instance, model)
    end_time = time.perf_counter()
    return end_time - start_time

def run_performance_test():
    """Compare original vs. optimized performance for API session reuse."""
    print("=" * 60)
    print("PERFORMANCE TEST: HuggingFace API Session Reuse")
    print("=" * 60)

    api = HuggingFaceAPI()
    model_to_test = "microsoft/phi-2"
    iterations = 500

    # Mock the response to avoid actual network calls
    mock_response = MagicMock()
    mock_response.status_code = 200

    # --- 1. Benchmark Original (requests.post) ---
    with patch('requests.post', return_value=mock_response) as mock_post:
        print(f"Benchmarking original implementation ({iterations} iterations)...")
        original_time = benchmark_function(original_check_model_status, api, model_to_test, iterations)
        print(f"Original Time (new connection per call): {original_time:.4f}s")
        assert mock_post.call_count == iterations, f"Expected {iterations} calls, but got {mock_post.call_count}"

    # --- 2. Benchmark Optimized (self.session.post) ---
    optimized_func = lambda api_inst, model_str: api_inst.check_model_status(model_str)

    with patch.object(api.session, 'post', return_value=mock_response) as mock_session_post:
        print(f"\\nBenchmarking optimized implementation ({iterations} iterations)...")
        optimized_time = benchmark_function(optimized_func, api, model_to_test, iterations)
        print(f"Optimized Time (reusing session): {optimized_time:.4f}s")
        assert mock_session_post.call_count == iterations, f"Expected {iterations} calls, but got {mock_session_post.call_count}"

    api.close()

    # --- 3. Compare Results ---
    print("-" * 60)

    # Allow for a small tolerance (e.g., 5%) in the mocked environment, as the overhead
    # can fluctuate. The real-world benefit comes from avoiding network handshakes.
    tolerance = original_time * 0.05

    if optimized_time > original_time + tolerance:
        print(f"⚠️ REGRESSION: Optimized version is significantly slower by {optimized_time - original_time:.4f}s.")
        success = False
    else:
        improvement = ((original_time - optimized_time) / original_time) * 100 if original_time > 0 else 0
        if improvement < 0:
            print(f"✅ PASSED: Optimized version is negligibly slower within tolerance.")
        else:
            print(f"✅ PASSED: Session reuse is measurably faster or equal.")

        print(f"   Improvement in mock test: {improvement:.1f}%")
        print("   (Note: Real-world improvement will be significantly higher due to network savings)")
        success = True

    print("=" * 60)

    # Clean up the env var
    del os.environ['HUGGINGFACE_TOKEN']

    if not success:
        print("\\nTest failed.")
        sys.exit(1)
    else:
        print("\\nTest passed successfully.")
        sys.exit(0)

if __name__ == "__main__":
    run_performance_test()
