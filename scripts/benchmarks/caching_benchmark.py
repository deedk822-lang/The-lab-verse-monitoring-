import timeit
import os
import sys

# Setup string for the "old" way.
SETUP_OLD = """
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from vaal_ai_empire.services.content_generator import ContentFactory
"""

# Code to execute for the "old" way.
CODE_OLD = """
for _ in range(10):
    _ = ContentFactory()
"""

# Setup string for the "new" way.
SETUP_NEW = """
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from vaal_ai_empire.services.content_generator import content_factory
"""

# Code to execute for the "new" way.
CODE_NEW = """
for _ in range(10):
    _ = content_factory
"""


def run_benchmark():
    """Runs a benchmark comparing the two approaches."""
    print("=" * 60)
    print("⚡ Bolt: ContentFactory Singleton Performance Benchmark")
    print("=" * 60)
    print("Running a more realistic benchmark using timeit...")

    # Time the execution of each approach
    old_time = timeit.timeit(CODE_OLD, setup=SETUP_OLD, number=100)
    new_time = timeit.timeit(CODE_NEW, setup=SETUP_NEW, number=100)


    # Calculate and display results
    if new_time > 0 and old_time > new_time:
        improvement = ((old_time - new_time) / old_time) * 100
    else:
        improvement = 0

    print("\n" + "-" * 60)
    print("📊 BENCHMARK RESULTS")
    print("-" * 60)
    print(f"Original Instantiation Time:\t{old_time:.4f}s")
    print(f"Optimized Singleton Time:\t{new_time:.4f}s")
    print("-" * 60)

    if improvement > 1:
        print(f"✅ PASSED: The optimized approach is {improvement:.2f}% faster.")
        return True
    else:
        print("❌ FAILED: Optimization did not yield a significant improvement.")
        return False

if __name__ == "__main__":
    success = run_benchmark()
    sys.exit(0 if success else 1)
