
import sys
import os
import time
from unittest.mock import patch, MagicMock

# Add the vaal-ai-empire directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the optimized class
from api.image_generation import ImageGenerator

# --- Mocking for Benchmark ---
def mocked_generate(self, prompt, style="professional"):
    """Simulate a network-bound API call with 500ms delay"""
    time.sleep(0.5)
    return {"image_url": f"url_{prompt[:5]}", "provider": "mock"}

class SequentialImageGenerator(ImageGenerator):
    """A version of ImageGenerator that runs batch sequentially for comparison"""
    def generate_batch(self, prompts, style="professional"):
        results = []
        for prompt in prompts:
            results.append(self.generate(prompt, style=style))
        return results

def run_benchmark():
    print("=" * 60)
    print("⚡ BOLT PERFORMANCE BENCHMARK: Image Batch Generation")
    print("=" * 60)

    prompts = [f"Business prompt {i}" for i in range(5)]
    print(f"Batch size: {len(prompts)} images")
    print(f"Simulated latency: 500ms per image")
    print("-" * 60)

    # 1. Benchmark Sequential (Simulated Original)
    with patch.object(ImageGenerator, 'generate', mocked_generate):
        seq_generator = SequentialImageGenerator()
        print("Running sequential generation...")
        start = time.perf_counter()
        seq_results = seq_generator.generate_batch(prompts)
        seq_duration = time.perf_counter() - start
        seq_generator.close()

    # 2. Benchmark Parallel (Optimized)
    with patch.object(ImageGenerator, 'generate', mocked_generate):
        par_generator = ImageGenerator()
        print("Running parallel generation (Bolt optimized)...")
        start = time.perf_counter()
        par_results = par_generator.generate_batch(prompts)
        par_duration = time.perf_counter() - start
        par_generator.close()

    # --- Results ---
    improvement = ((seq_duration - par_duration) / seq_duration) * 100

    print("-" * 60)
    print(f"Original (Sequential): {seq_duration:.4f}s")
    print(f"Optimized (Parallel):   {par_duration:.4f}s")
    print(f"🚀 Improvement: {improvement:.2f}% faster")
    print("=" * 60)

    # Verification of results
    if len(par_results) == len(prompts) and par_duration < seq_duration:
        print("✅ SUCCESS: Performance improvement verified!")
        # Benchmark Results:
        # Original (Sequential): ~2.50s
        # Optimized (Parallel):   ~0.51s
        # Improvement: ~80% faster
        return True, improvement
    else:
        print("❌ FAILURE: No significant improvement measured.")
        return False, improvement

if __name__ == "__main__":
    success, imp = run_benchmark()
    # Write results to a file for documentation
    with open("benchmark_results.txt", "w") as f:
        f.write(f"Improvement: {imp:.2f}% faster\n")
