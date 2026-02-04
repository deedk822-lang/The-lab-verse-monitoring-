
import sys
import os
import time
import logging
import concurrent.futures

# Add the project root to sys.path
sys.path.append(os.path.join(os.getcwd(), "vaal-ai-empire"))

from api.cohere import CohereAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def benchmark_email_sequence():
    print("=" * 60)
    print("BENCHMARKING CohereAPI.generate_email_sequence")
    print("=" * 60)

    # Force mock generate_content to simulate delay and avoid API calls
    class MockCohereAPI(CohereAPI):
        def __init__(self):
            # Don't call super().__init__ to avoid API key checks
            self.usage_log = []
            pass

        def generate_content(self, prompt, max_tokens=300, system_message=None):
            time.sleep(1) # Simulate 1s per email
            return {"text": "Subject: Day X\nBody: Hello", "usage": {}}

    api = MockCohereAPI()

    days = 5
    print(f"\nGenerating {days}-day email sequence...")
    start_time = time.perf_counter()
    api.generate_email_sequence("butchery", days=days)
    total_time = time.perf_counter() - start_time

    print(f"Total Time for {days} days: {total_time:.4f}s")

    # If it was sequential, it would take ~5s (1s * 5)
    # If parallel with max_workers=5, it should take ~1s

    if total_time < 2:
        print("\n✓ SUCCESS: Performance is parallelized")
    else:
        print("\n⚠️ FAILURE: Performance seems sequential")

if __name__ == "__main__":
    benchmark_email_sequence()
