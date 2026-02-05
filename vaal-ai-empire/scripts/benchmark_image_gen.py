
import time
import sys
import os
from unittest.mock import patch

# Adjust sys.path to find the vaal-ai-empire package
# We assume this script is in vaal-ai-empire/scripts/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.image_generation import ImageGenerator

def benchmark_function(prompts):
    """Benchmark the generate_batch function"""
    generator = ImageGenerator()

    # Mock the generate method to simulate a slow API call (0.5 second)
    # This allows us to measure the overhead of sequential vs parallel execution
    # without needing actual API keys or waiting too long.
    with patch.object(ImageGenerator, 'generate', side_effect=lambda p, style='professional': (time.sleep(0.5), {"image_url": "mock_url", "provider": "mock", "cost_usd": 0.0})[1]):
        start = time.perf_counter()
        results = generator.generate_batch(prompts)
        end = time.perf_counter()

    return end - start, results

def test_optimization():
    print("=" * 60)
    print("⚡ BOLT PERFORMANCE BENCHMARK: Image Generation Batch ⚡")
    print("=" * 60)

    prompts = [f"Business image prompt {i}" for i in range(5)]
    print(f"Testing with {len(prompts)} prompts (simulating 0.5s per image)")

    duration, results = benchmark_function(prompts)

    print("-" * 60)
    print(f"Total duration: {duration:.4f}s")
    print(f"Average per image: {duration/len(prompts):.4f}s")
    print("-" * 60)

    if duration < 1.0: # If parallelized, it should be close to 0.5s + small overhead
        print("✅ RESULT: Parallel execution detected!")
        return True
    else:
        print("❌ RESULT: Sequential execution detected.")
        return False

if __name__ == "__main__":
    success = test_optimization()
    # We exit with 0 to allow the baseline to "pass" even if sequential,
    # but we'll use the output to judge.
    sys.exit(0)
