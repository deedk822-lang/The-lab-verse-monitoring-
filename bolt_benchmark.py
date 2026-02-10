import time
import sys
import os
import logging
from unittest.mock import patch, MagicMock

# Add the project directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'vaal-ai-empire')))

from api.image_generation import ImageGenerator

# Configure logging to be quiet
logging.basicConfig(level=logging.ERROR)

def benchmark_generate_batch(generator, prompts, iterations=1):
    start_time = time.perf_counter()
    for _ in range(iterations):
        results = generator.generate_batch(prompts)
    end_time = time.perf_counter()
    return end_time - start_time, results

def test_optimization():
    print("=" * 60)
    print("⚡ BOLT: Image Generation Performance Benchmark")
    print("=" * 60)

    generator = ImageGenerator()
    prompts = [f"Business image {i}" for i in range(5)]

    # Mock 'generate' to simulate API latency
    def mocked_generate(prompt, style="professional", provider="auto"):
        time.sleep(0.5) # Simulate 500ms API latency
        return {
            "image_url": f"mocked_url_{prompt}",
            "provider": "mocked",
            "cost_usd": 0.01,
            "prompt": prompt
        }

    with patch.object(ImageGenerator, 'generate', side_effect=mocked_generate):
        print(f"Benchmarking batch generation of {len(prompts)} images with 0.5s simulated latency each...")

        # We need to simulate sequential execution for baseline comparison
        # Since we've already changed the code to parallel, we'll manually simulate sequential here
        start_seq = time.perf_counter()
        seq_results = []
        for p in prompts:
            seq_results.append(mocked_generate(p))
        seq_time = time.perf_counter() - start_seq

        print(f"Simulated Sequential Time (Baseline): {seq_time:.4f}s")

        # Parallel (new optimized version)
        par_time, par_results = benchmark_generate_batch(generator, prompts)
        print(f"Optimized Parallel Time:             {par_time:.4f}s")

        # --- Correctness Check ---
        assert len(par_results) == len(seq_results), "Results length mismatch!"
        for i in range(len(prompts)):
            assert par_results[i]["prompt"] == prompts[i], f"Result {i} prompt mismatch!"
            assert par_results[i]["image_url"] == f"mocked_url_{prompts[i]}", f"Result {i} URL mismatch!"

        print("✅ Correctness verified: Results match and order is preserved.")

        # --- Improvement Check ---
        improvement = ((seq_time - par_time) / seq_time) * 100
        print(f"🚀 Improvement: {improvement:.2f}% faster")

        if improvement > 50:
            print("✅ SIGNIFICANT IMPROVEMENT DETECTED")
            return True
        else:
            print("⚠️ Minor or no improvement detected.")
            return False

if __name__ == "__main__":
    success = test_optimization()
    sys.exit(0 if success else 1)
