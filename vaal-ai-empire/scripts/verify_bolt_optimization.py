import time
import sys
import os
import logging
from unittest.mock import MagicMock, patch
from typing import Dict, List

# Add parent directory to path to import api
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from api.image_generation import ImageGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify_bolt")

def mock_generate_api_call(*args, **kwargs):
    """Simulate a slow API call"""
    time.sleep(0.5)  # Simulate 500ms latency
    mock_response = MagicMock()
    mock_response.status_code = 200
    # Return some fake data depending on the URL
    if "stability.ai" in args[0]:
        mock_response.json.return_value = {"artifacts": [{"base64": "ZmFrZV9pbWFnZV9kYXRh"}]} # "fake_image_data"
    else:
        mock_response.content = b"fake_image_data"
    return mock_response

def benchmark_sequential(generator, prompts):
    start = time.perf_counter()
    results = []
    for prompt in prompts:
        # We call generate directly to simulate sequential behavior
        # though generate_batch is what we want to test.
        # But we want to compare against the NEW parallel generate_batch.
        results.append(generator.generate(prompt))
    end = time.perf_counter()
    return end - start, results

def benchmark_parallel(generator, prompts):
    start = time.perf_counter()
    results = generator.generate_batch(prompts)
    end = time.perf_counter()
    return end - start, results

@patch('api.image_generation.requests.Session')
@patch('api.image_generation.Path.mkdir') # Avoid creating real directories
@patch('api.image_generation.open', create=True) # Avoid writing real files
def test_performance(mock_open, mock_mkdir, mock_session_class):
    print("=" * 60)
    print("⚡ BOLT PERFORMANCE VERIFICATION ⚡")
    print("=" * 60)

    # Setup mock session
    mock_session = mock_session_class.return_value
    mock_session.post.side_effect = mock_generate_api_call
    mock_session.get.side_effect = mock_generate_api_call

    # Initialize generator with all providers "available"
    with patch.dict(os.environ, {
        "STABILITY_API_KEY": "test",
        "REPLICATE_API_TOKEN": "test",
        "HUGGINGFACE_TOKEN": "test"
    }):
        # Mock _check_local_sd to be fast
        with patch.object(ImageGenerator, '_check_local_sd', return_value=True):
            generator = ImageGenerator()

    prompts = [f"Prompt {i}" for i in range(5)]

    print(f"Generating {len(prompts)} images...")

    # Measure Sequential (simulated by loop)
    print("\nRunning Sequential Benchmark...")
    seq_time, _ = benchmark_sequential(generator, prompts)
    print(f"Sequential Time: {seq_time:.4f}s")

    # Measure Parallel (using the optimized generate_batch)
    print("\nRunning Parallel Benchmark (Optimized)...")
    par_time, _ = benchmark_parallel(generator, prompts)
    print(f"Parallel Time: {par_time:.4f}s")

    improvement = ((seq_time - par_time) / seq_time) * 100
    print(f"\nSpeedup: {improvement:.2f}%")

    # Verify correctness of skip_enhance
    print("\nVerifying skip_enhance logic...")
    with patch.object(generator, '_enhance_prompt', wraps=generator._enhance_prompt) as mock_enhance:
        # First call: should enhance
        generator.generate("test prompt")
        assert mock_enhance.call_count == 1

        # Second call with skip_enhance=True: should NOT enhance
        generator.generate("test prompt", skip_enhance=True)
        assert mock_enhance.call_count == 1
        print("✓ skip_enhance logic verified: Double enhancement prevented.")

    if par_time < seq_time * 0.5: # Expecting at least 2x speedup for 5 items with 5 workers
        print("\n✅ SUCCESS: Parallel generation is significantly faster!")
        return True
    else:
        print("\n⚠️ WARNING: Parallel generation speedup was less than expected.")
        return par_time < seq_time

if __name__ == "__main__":
    success = test_performance()
    sys.exit(0 if success else 1)
