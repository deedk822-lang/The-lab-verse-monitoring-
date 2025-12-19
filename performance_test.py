# performance_test.py
import time
import sys
from unittest.mock import patch, MagicMock

# Temporarily add the project directory to the Python path to allow imports
sys.path.insert(0, './vaal-ai-empire')

from api.image_generation import ImageGenerator

def generate_batch_original(image_generator_instance, prompts: list[str], style: str = "professional") -> list[dict]:
    """The original, sequential implementation for benchmarking."""
    results = []
    for i, prompt in enumerate(prompts):
        try:
            # Add the prompt to the result to make order verification easier
            result = image_generator_instance.generate(prompt, style=style)
            result['prompt'] = prompt
            results.append(result)
        except Exception as e:
            results.append({
                "image_url": "placeholder", "provider": "error", "cost_usd": 0.0, "error": str(e), "prompt": prompt
            })
    return results

def benchmark_function(func, *args, **kwargs):
    """Benchmark a function and return its execution time."""
    start_time = time.perf_counter()
    func(*args, **kwargs)
    end_time = time.perf_counter()
    return end_time - start_time

def test_optimization():
    """Compare original vs. optimized performance for image generation."""
    print("=" * 60)
    print("⚡ Bolt: Performance Comparison Test ⚡")
    print("=" * 60)

    prompts = [f"Test prompt {i}" for i in range(5)]
    image_generator = ImageGenerator()

    # Mock the actual image generation to simulate network latency without API calls
    # This prevents real API calls and standardizes the benchmark.
    def mock_generate_with_delay(prompt, style):
        time.sleep(0.5)  # Simulate a 500ms network call
        return {"image_url": "mocked_url", "provider": "mock", "cost_usd": 0.0, "prompt": prompt}

    with patch.object(image_generator, 'generate', side_effect=mock_generate_with_delay) as patched_generate:
        # Benchmark Original (Sequential)
        print(f"🔬 Testing ORIGINAL sequential implementation with {len(prompts)} images...")
        original_time = benchmark_function(generate_batch_original, image_generator, prompts)
        print(f"  -> Original Time: {original_time:.4f}s")

        # Benchmark Optimized (Concurrent)
        print(f"\n🔬 Testing OPTIMIZED concurrent implementation with {len(prompts)} images...")
        optimized_time = benchmark_function(image_generator.generate_batch, prompts)
        print(f"  -> Optimized Time: {optimized_time:.4f}s")

        # --- Verification ---
        print("\n" + "="*25 + " RESULTS " + "="*26)

        # Correctness and Order Check
        original_results = generate_batch_original(image_generator, prompts)
        optimized_results = image_generator.generate_batch(prompts)

        assert len(original_results) == len(optimized_results), f"Results count mismatch! Original: {len(original_results)}, Optimized: {len(optimized_results)}"

        original_prompts_order = [res.get('prompt') for res in original_results]
        optimized_prompts_order = [res.get('prompt') for res in optimized_results]

        assert original_prompts_order == optimized_prompts_order, "Order regression detected! The results are not in the same order as the prompts."
        print(f"✅ Correctness & Order Verified: Both methods produced {len(optimized_results)} results in the correct order.")

    # Performance Comparison
    if optimized_time >= original_time:
        print("⚠️ NO IMPROVEMENT - Optimization may not be effective.")
        improvement = 0
    else:
        improvement = ((original_time - optimized_time) / original_time) * 100
        print(f"🚀 Improvement: {improvement:.1f}% faster")

    if improvement > 40: # Expecting significant improvement due to parallelization
        print("✅ SIGNIFICANT PERFORMANCE IMPROVEMENT DETECTED!")
        success = True
    elif improvement > 10:
        print("✅ Minor improvement noted.")
        success = True
    else:
        print("❌ Test Failed: No significant improvement.")
        success = False

    print("=" * 60)

    return success

if __name__ == "__main__":
    # The script needs `vaal-ai-empire` to be importable.
    # This is handled by adding it to sys.path at the top.
    try:
        success = test_optimization()
        sys.exit(0 if success else 1)
    except ImportError as e:
        print(f"\n❌ ERROR: Could not import the necessary module: {e}", file=sys.stderr)
        print("Please ensure you run this script from the repository root.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)
