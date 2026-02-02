import time
import sys
import os
import logging
from unittest.mock import MagicMock, patch

# Add the project root and vaal-ai-empire to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.image_generation import ImageGenerator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def mock_generate_stability(self, prompt):
    """Mock stability generation with a small delay"""
    time.sleep(1.0)  # Simulate I/O delay
    return {
        "image_url": "mock_stability.png",
        "provider": "stability",
        "cost_usd": 0.02,
        "prompt": prompt
    }

def run_benchmark():
    print("=" * 60)
    print("⚡ BOLT: PERFORMANCE OPTIMIZATION BENCHMARK ⚡")
    print("=" * 60)

    # Test proper instantiation (checks for AttributeError)
    print("1. Testing instantiation...")
    try:
        with patch('api.image_generation.requests.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            # Mock _detect_available_providers to avoid real network calls during init
            with patch.object(ImageGenerator, '_detect_available_providers', return_value={"stability": True}):
                generator = ImageGenerator()
                print("✅ SUCCESS: ImageGenerator instantiated correctly.")
    except Exception as e:
        print(f"❌ FAILURE: Instantiation failed: {e}")
        return False

    # Mock the providers to ensure at least one is "available"
    with patch.object(ImageGenerator, '_detect_available_providers', return_value={"stability": True, "replicate": False, "huggingface": False, "local": False}):
        with patch.object(ImageGenerator, '_generate_stability', side_effect=mock_generate_stability, autospec=True):
            generator = ImageGenerator()

            prompts = [f"Prompt {i}" for i in range(5)]

            print(f"\n2. Testing Parallel Batch Generation ({len(prompts)} images)...")
            start_time = time.perf_counter()
            results = generator.generate_batch(prompts)
            end_time = time.perf_counter()

            parallel_time = end_time - start_time
            print(f"Parallel Batch Time: {parallel_time:.4f}s")

            # Verify results
            assert len(results) == 5
            for r in results:
                assert r["provider"] == "stability"

            print(f"\n3. Comparing with Sequential (Simulated)...")
            # In the original code, 5 images with 1.0s delay each would take 5.0s
            sequential_time = 5.0
            print(f"Estimated Sequential Time: {sequential_time:.4f}s")

            improvement = ((sequential_time - parallel_time) / sequential_time) * 100
            print(f"\nSpeedup: {improvement:.1f}% faster")

            if parallel_time < 2.0: # Should be around 1.0s + overhead
                print("✅ SUCCESS: Parallel execution verified!")
            else:
                print("⚠️ WARNING: Parallel execution might not be working as expected.")

            print("\n4. Testing empty batch handling...")
            try:
                empty_results = generator.generate_batch([])
                assert empty_results == []
                print("✅ SUCCESS: Empty batch handled correctly.")
            except Exception as e:
                print(f"❌ FAILURE: Empty batch caused error: {e}")

            print("\n5. Verifying skip_enhance logic...")
            with patch.object(ImageGenerator, '_enhance_prompt', side_effect=lambda p, s: f"{p}, enhanced") as mock_enhance:
                # Force fallback by making stability fail once
                generator.providers["stability"] = False
                generator.providers["local"] = True

                with patch.object(ImageGenerator, '_generate_local', return_value={"provider": "local"}) as mock_local:
                    result = generator.generate("Test Prompt")

                    # Call count should be 1 (only the initial enhance)
                    # Without skip_enhance, it would be called again in _generate_fallback
                    print(f"Enhance call count: {mock_enhance.call_count}")
                    if mock_enhance.call_count == 1:
                        print("✅ SUCCESS: skip_enhance prevents double-enhancement!")
                    else:
                        print(f"❌ FAILURE: _enhance_prompt called {mock_enhance.call_count} times.")

    print("=" * 60)
    return improvement > 0

if __name__ == "__main__":
    success = run_benchmark()
    sys.exit(0 if success else 1)
