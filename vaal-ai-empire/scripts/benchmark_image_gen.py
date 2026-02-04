import time
import sys
import os
from unittest.mock import patch

# Add the parent directory to sys.path to allow importing from api
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from api.image_generation import ImageGenerator

def mock_generate(self, prompt, style="professional", provider="auto"):
    # Simulate a slow API call
    time.sleep(1.0)
    return {
        "image_url": f"mock_url_{prompt[:5]}",
        "provider": "mock",
        "cost_usd": 0.01
    }

def sequential_generate_batch(generator, prompts, style="professional"):
    """Recreation of the original unoptimized sequential generate_batch"""
    results = []
    for i, prompt in enumerate(prompts):
        try:
            result = generator.generate(prompt, style=style)
            results.append(result)
        except Exception as e:
            results.append({"error": str(e)})
    return results

def main():
    print("=" * 60)
    print("⚡ BOLT PERFORMANCE BENCHMARK: ImageGenerator.generate_batch ⚡")
    print("=" * 60)

    prompts = [f"Prompt {i}" for i in range(5)]

    # We patch the generate method to simulate slow API calls
    with patch.object(ImageGenerator, 'generate', autospec=True, side_effect=mock_generate):
        generator = ImageGenerator()

        print(f"Benchmarking with {len(prompts)} prompts (1.0s delay each)...")

        # 1. Original Sequential Implementation
        print("\n1. Running Original (Sequential)...")
        start_seq = time.perf_counter()
        sequential_generate_batch(generator, prompts)
        duration_seq = time.perf_counter() - start_seq
        print(f"   Duration: {duration_seq:.4f}s")

        # 2. Optimized Parallel Implementation
        print("\n2. Running Optimized (Parallel with ThreadPoolExecutor)...")
        start_par = time.perf_counter()
        generator.generate_batch(prompts)
        duration_par = time.perf_counter() - start_par
        print(f"   Duration: {duration_par:.4f}s")

        # Calculate improvement
        improvement = ((duration_seq - duration_par) / duration_seq) * 100

        print("\n" + "=" * 60)
        print("RESULTS SUMMARY")
        print("-" * 60)
        print(f"Original Time:  {duration_seq:.4f}s")
        print(f"Optimized Time: {duration_par:.4f}s")
        print(f"IMPROVEMENT:    {improvement:.1f}% faster")
        print("=" * 60)

        if improvement > 50:
            print("✅ Bolt: Significant performance boost achieved!")

if __name__ == "__main__":
    main()
