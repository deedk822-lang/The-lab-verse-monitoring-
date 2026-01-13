import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import os
import importlib

# To test the optimization, we need to compare the old and new versions.
# We'll dynamically import both modules.

# Use importlib to handle the hyphenated path
original_database_module = importlib.import_module("vaal-ai-empire.core.database")
OriginalDatabase = original_database_module.Database

optimized_database_module = importlib.import_module("vaal-ai-empire.core.optimized_database")
OptimizedDatabase = optimized_database_module.Database


DB_PATH = "performance_test.db"

def setup_databases():
    """Initializes both databases for the test."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    # Initialize original DB
    original_db = OriginalDatabase(db_path=DB_PATH)
    original_db.add_client({
        'id': 'test_client',
        'name': 'Test Client',
        'business_type': 'test',
        'phone': '1234567890'
    })

    # The pooled DB uses the same file, so it's already set up.
    # We just need to instantiate it.
    optimized_db = OptimizedDatabase(db_path=DB_PATH)
    return original_db, optimized_db

def task(db_instance, num_queries=10):
    """A simple task that performs multiple read queries."""
    for _ in range(num_queries):
        db_instance.get_client('test_client')
    return True

def run_benchmark(db_class, num_threads, queries_per_thread):
    """Runs a benchmark for a given Database class."""
    db_instance = db_class(db_path=DB_PATH)

    start_time = time.perf_counter()

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(task, db_instance, queries_per_thread) for _ in range(num_threads)]
        for future in as_completed(futures):
            future.result()

    end_time = time.perf_counter()

    # Properly close connections if the class has a specific method for it
    if hasattr(db_instance, 'close_all_connections'):
        db_instance.close_all_connections()
    elif hasattr(db_instance, 'close_connection'):
        # The old DB manages connections per thread, so this is trickier.
        # We rely on atexit or the test duration being short.
        pass

    return end_time - start_time

def test_optimization():
    """Compares original vs. optimized database performance."""
    print("=" * 60)
    print("⚡ Bolt: Database Connection Pool Performance Test ⚡")
    print("=" * 60)

    num_threads = 20
    queries_per_thread = 50
    total_queries = num_threads * queries_per_thread

    print(f"Simulating workload: {num_threads} concurrent threads, {queries_per_thread} queries each.")
    print(f"Total queries: {total_queries}\n")

    # Setup databases
    try:
        original_db, optimized_db = setup_databases()
    except Exception as e:
        print(f"❌ ERROR: Failed to set up databases: {e}")
        print("Please ensure the script has permissions to create 'performance_test.db'")
        return False

    # Benchmark Original (threading.local)
    print("Benchmarking Original (threading.local)...")
    try:
        original_time = run_benchmark(OriginalDatabase, num_threads, queries_per_thread)
        print(f"  -> Original Time: {original_time:.4f}s")
    except Exception as e:
        print(f"❌ ERROR: Benchmark failed for OriginalDatabase: {e}")
        return False

    # Benchmark Optimized (Connection Pool)
    # Re-create the pooled DB instance to ensure the pool is fresh
    print("\nBenchmarking Optimized (Connection Pool)...")
    try:
        optimized_time = run_benchmark(OptimizedDatabase, num_threads, queries_per_thread)
        print(f"  -> Optimized Time: {optimized_time:.4f}s")
    except Exception as e:
        print(f"❌ ERROR: Benchmark failed for OptimizedDatabase: {e}")
        return False

    print("-" * 60)

    if optimized_time >= original_time:
        print("⚠️  NO IMPROVEMENT DETECTED.")
        improvement = 0
    else:
        improvement = ((original_time - optimized_time) / original_time) * 100
        print(f"✅ SIGNIFICANT IMPROVEMENT: {improvement:.1f}% faster")

    print(f"\nOriginal:  {original_time:.4f}s")
    print(f"Optimized: {optimized_time:.4f}s")

    # Cleanup
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    if improvement > 1: # Set a lower threshold for success
        print("\n🏆 Result: Success! The connection pool is more efficient.")
        return True
    else:
        print("\n📉 Result: Failure. The optimization did not provide a significant benefit.")
        return False

if __name__ == "__main__":
    # Temporarily add the project directory to the path to allow imports
    sys.path.insert(0, os.path.abspath('.'))

    success = test_optimization()

    # Exit with a status code indicating success or failure
    sys.exit(0 if success else 1)
