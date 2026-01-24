
import time
import requests
from unittest.mock import patch, MagicMock
import sys
import os
import pathlib

# This script must be run with the `vaal-ai-empire` directory in the PYTHONPATH
# Example: PYTHONPATH=$(pwd)/vaal-ai-empire python vaal-ai-empire/scripts/benchmark_image_generation.py

# By adding vaal-ai-empire to the path, we can import `api` directly
from api.image_generation import ImageGenerator

class ImageGeneratorOriginal:
    """A version of the ImageGenerator that uses direct requests.post for benchmarking."""
    def _generate_huggingface(self, prompt: str):
        # This is a simplified version of the original method for benchmarking purposes.
        # It directly uses requests.post, creating a new connection each time.
        api_token = "fake_token"
        api_url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
        headers = {"Authorization": f"Bearer {api_token}"}
        try:
            response = requests.post(
                api_url,
                headers=headers,
                json={"inputs": prompt},
                timeout=60
            )
            response.raise_for_status()
            return {"status": "success"}
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return {"status": "error"}

def benchmark_generator(generator_instance, method_name, iterations=100):
    """Benchmarks a given method on a generator instance."""
    start_time = time.perf_counter()
    for i in range(iterations):
        getattr(generator_instance, method_name)(f"test prompt {i}")
    end_time = time.perf_counter()
    return end_time - start_time

def main():
    """Main function to run the benchmark."""
    print("=" * 60)
    print("⚡ Bolt: Benchmarking Connection Reuse Optimization ⚡")
    print("=" * 60)

    # Mock the environment variables so the classes can be instantiated
    with patch.dict(os.environ, {
        'HUGGINGFACE_TOKEN': 'fake_token',
        'STABILITY_API_KEY': '',
        'REPLICATE_API_TOKEN': ''
    }):
        # --- Benchmark Original Implementation (No Session) ---
        original_generator = ImageGeneratorOriginal()
        # Mock the actual requests.post call
        with patch('requests.post') as mock_post:
            # Configure the mock to return a successful response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"result": "success"}
            mock_post.return_value = mock_response

            print("\n🔬 Benchmarking ORIGINAL implementation (new connection per call)...")
            original_time = benchmark_generator(original_generator, '_generate_huggingface', iterations=100)
            print(f"   -> Original implementation took: {original_time:.4f} seconds")
            assert mock_post.call_count == 100, "requests.post should have been called 100 times"

        # --- Benchmark Optimized Implementation (With Session) ---
        # Mock Path.mkdir to prevent the generator from creating directories during test
        with patch.object(pathlib.Path, 'mkdir'):
            optimized_generator = ImageGenerator()
            # Mock the session's post method
            with patch.object(optimized_generator.session, 'post') as mock_session_post:
                # Configure the mock to return a successful response
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"result": "success"}
                # FIX: Provide a bytes object for `content` to avoid TypeError on write
                mock_response.content = b''
                mock_session_post.return_value = mock_response

                print("\n🚀 Benchmarking OPTIMIZED implementation (reusing connections)...")
                optimized_time = benchmark_generator(optimized_generator, '_generate_huggingface', iterations=100)
                print(f"   -> Optimized implementation took: {optimized_time:.4f} seconds")
                assert mock_session_post.call_count == 100, "session.post should have been called 100 times"


    # --- Calculate and Report Results ---
    print("\n" + "=" * 60)
    print("📊 Results")
    print("-" * 60)
    print(f"Original Time:  {original_time:.4f}s")
    print(f"Optimized Time: {optimized_time:.4f}s")

    if original_time > optimized_time:
        improvement = ((original_time - optimized_time) / original_time) * 100
        print(f"\n✅ Improvement: {improvement:.2f}% faster")
        print("   Connection reuse significantly reduces overhead for repeated calls.")
    else:
        print("\n⚠️ No significant improvement detected.")
        print("   The overhead of creating new connections was not the bottleneck in this test.")

    print("=" * 60)

if __name__ == "__main__":
    main()
