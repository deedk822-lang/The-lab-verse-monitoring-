# performance_test.py
import time
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import MagicMock

# --- Mocks to simulate real classes ---

class MockSocialPoster:
    """A mock poster that simulates network latency."""
    def post_via_ayrshare(self, content, platforms, image_url=None):
        time.sleep(0.1)  # Simulate a 100ms network call
        return {"status": "success"}

class MockContentScheduler:
    """A mock scheduler that returns a fixed list of posts."""
    def __init__(self, posts):
        self._posts = posts
        self._posted_ids = set()

    def get_due_posts(self):
        return self._posts

    def mark_posted(self, post_id):
        self._posted_ids.add(post_id)

# --- Implementations to test ---

# 1. Original Sequential Implementation
def post_scheduled_content_original(scheduler, poster):
    due_posts = scheduler.get_due_posts()
    for post in due_posts:
        try:
            platforms = post["platforms"].split(",")
            result = poster.post_via_ayrshare(
                post["content"],
                platforms,
                post.get("image_url")
            )
            if result.get("status") != "error":
                scheduler.mark_posted(post["id"])
        except Exception:
            pass # Ignore errors in test

# 2. New Parallel Implementation
def _post_single_item_parallel(post, scheduler, poster):
    try:
        platforms = post["platforms"].split(",")
        result = poster.post_via_ayrshare(
            post["content"],
            platforms,
            post.get("image_url")
        )
        if result.get("status") != "error":
            scheduler.mark_posted(post["id"])
            return post["id"], True
        return post["id"], False
    except Exception:
        return post["id"], False

def post_scheduled_content_optimized(scheduler, poster):
    due_posts = scheduler.get_due_posts()
    if not due_posts:
        return

    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_post = {executor.submit(_post_single_item_parallel, post, scheduler, poster): post for post in due_posts}
        for future in as_completed(future_to_post):
            future.result()

# --- Benchmark ---

def benchmark_function(func, scheduler, poster):
    """Benchmark a function's execution time."""
    start = time.perf_counter()
    func(scheduler, poster)
    end = time.perf_counter()
    return end - start

def run_benchmark():
    """Compare original vs optimized performance."""
    print("=" * 60)
    print("⚡ Bolt: Performance Benchmark")
    print("Target: Parallelizing social media posting")
    print("=" * 60)

    # Setup
    num_posts = 50
    print(f"Simulating {num_posts} posts, each with 100ms network latency...")
    dummy_posts = [{"id": i, "content": f"Post {i}", "platforms": "facebook,twitter", "client_id": "test"} for i in range(num_posts)]

    poster = MockSocialPoster()

    # Benchmark Original
    scheduler_orig = MockContentScheduler(dummy_posts)
    original_time = benchmark_function(post_scheduled_content_original, scheduler_orig, poster)

    # Benchmark Optimized
    scheduler_opt = MockContentScheduler(dummy_posts)
    optimized_time = benchmark_function(post_scheduled_content_optimized, scheduler_opt, poster)

    # Verify correctness
    assert scheduler_orig._posted_ids == scheduler_opt._posted_ids, "Mismatch in posted items!"
    print("\n✓ Correctness verified: Both methods posted the same items.")

    # Show results
    improvement = ((original_time - optimized_time) / original_time) * 100 if original_time > 0 else 0

    print("\n--- BENCHMARK RESULTS ---")
    print(f"Original (Sequential): {original_time:.4f}s")
    print(f"Optimized (Parallel):  {optimized_time:.4f}s")
    print("-------------------------")
    print(f"🚀 Improvement: {improvement:.1f}% faster")

    if improvement > 50:
        print("\n🏆 STATUS: SIGNIFICANT IMPROVEMENT")
        return True
    else:
        print("\n STATUS: No significant improvement.")
        return False

if __name__ == "__main__":
    success = run_benchmark()
    sys.exit(0 if success else 1)
