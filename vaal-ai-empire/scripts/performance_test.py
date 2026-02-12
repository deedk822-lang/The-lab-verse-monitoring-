import logging
import os
import sys
import time

# Add the project root to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

try:
    from api.image_generation import ImageGenerator
except ImportError:
    # Handle direct script execution vs module
    sys.path.append(os.path.join(os.getcwd(), "vaal-ai-empire"))
    from api.image_generation import ImageGenerator

logging.basicConfig(level=logging.INFO)


def benchmark_batch_generation():
    print("=" * 60)
    print("PERFORMANCE COMPARISON: SEQUENTIAL VS PARALLEL")
    print("=" * 60)

    generator = ImageGenerator()
    prompts = [f"Prompt {i}" for i in range(5)]

    # Mock self.generate to simulate network delay
    original_generate = generator.generate

    def mocked_generate(prompt, style="professional", provider="auto"):
        time.sleep(1)  # Simulate 1 second delay
        return {"provider": "mock", "image_url": "mock_url", "cost_usd": 0.0}

    generator.generate = mocked_generate

    # Measure Sequential
    print("\nRunning Sequential (Simulated)...")
    start_seq = time.perf_counter()
    seq_results = []
    for prompt in prompts:
        seq_results.append(generator.generate(prompt))
    end_seq = time.perf_counter()
    seq_time = end_seq - start_seq
    print(f"Sequential Time: {seq_time:.4f}s")

    # Measure Parallel
    print("\nRunning Parallel (Actual implementation)...")
    start_par = time.perf_counter()
    par_results = generator.generate_batch(prompts)
    end_par = time.perf_counter()
    par_time = end_par - start_par
    print(f"Parallel Time: {par_time:.4f}s")

    improvement = ((seq_time - par_time) / seq_time) * 100
    print(f"\nImprovement: {improvement:.1f}% faster")

    assert len(par_results) == len(prompts)
    print("\n✓ Benchmarking complete")

    # Restore original generate
    generator.generate = original_generate
    return improvement > 0


if __name__ == "__main__":
    success = benchmark_batch_generation()
    sys.exit(0 if success else 1)
