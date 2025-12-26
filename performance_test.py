import threading
import time
import os
import sqlite3
import sys
import importlib

# Correct path setup
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# Import the optimized database class
database_module = importlib.import_module("vaal-ai-empire.core.database")
OptimizedDatabase = database_module.Database

# --- Original Implementation for Benchmark ---
class OriginalDatabaseForTest:
    """A corrected version of the original threading.local() implementation for a fair benchmark."""
    def __init__(self, db_path):
        self.db_path = db_path
        self.thread_local = threading.local()
        # Prime the database with the table in a single, separate connection
        with sqlite3.connect(self.db_path, uri=True) as conn:
            conn.cursor().execute("CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY, name TEXT)")
            conn.commit()

    def get_connection(self):
        connection = getattr(self.thread_local, 'connection', None)
        if connection is None:
            # CRITICAL FIX: Add uri=True to connect to the shared in-memory DB
            connection = sqlite3.connect(self.db_path, check_same_thread=False, uri=True)
            self.thread_local.connection = connection
        return connection

    def query(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM test")
        cursor.fetchall()

    def close_thread_connection(self):
        connection = getattr(self.thread_local, 'connection', None)
        if connection:
            connection.close()

# --- Benchmark Runner ---
def run_benchmark(db_class, num_threads, num_queries, db_name):
    # A unique URI for each run to ensure they are isolated
    db_uri = f"file:{db_name}_{os.getpid()}?mode=memory&cache=shared"

    worker_func = None

    if db_class == OriginalDatabaseForTest:
        db = OriginalDatabaseForTest(db_uri)

        def worker():
            db.get_connection() # ensure connection exists for this thread
            barrier.wait()
            for _ in range(num_queries):
                db.query()
            db.close_thread_connection()
        worker_func = worker

    elif db_class == OptimizedDatabase:
        db = OptimizedDatabase(db_path=db_uri)
        with db.get_cursor() as cursor:
            cursor.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY, name TEXT)")

        def worker():
            barrier.wait()
            for _ in range(num_queries):
                with db.get_cursor() as cursor:
                     cursor.execute("SELECT * FROM test")
                     cursor.fetchall()
        worker_func = worker

    barrier = threading.Barrier(num_threads)
    threads = [threading.Thread(target=worker_func) for _ in range(num_threads)]

    start_time = time.perf_counter()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    end_time = time.perf_counter()

    # Clean up the pool if it exists, and reset the class variable for subsequent runs
    if hasattr(db, '_pool') and db._pool:
        db._pool.close_all_connections()
        OptimizedDatabase._pool = None

    return end_time - start_time

def main():
    """Run and compare benchmarks."""
    NUM_THREADS = 20
    NUM_QUERIES = 500

    print("="*50)
    print("⚡ Bolt: Database Connection Performance Test")
    print("="*50)
    print(f"Configuration: {NUM_THREADS} threads, {NUM_QUERIES} queries per thread")

    # Benchmark original implementation
    print("\nBenchmarking Original (threading.local)...")
    original_time = run_benchmark(OriginalDatabaseForTest, NUM_THREADS, NUM_QUERIES, "original_db")
    print(f"Original Time: {original_time:.4f}s")

    # Benchmark optimized implementation
    print("\nBenchmarking Optimized (Connection Pool)...")
    optimized_time = run_benchmark(OptimizedDatabase, NUM_THREADS, NUM_QUERIES, "optimized_db")
    print(f"Optimized Time: {optimized_time:.4f}s")

    # Calculate and display improvement
    improvement = ((original_time - optimized_time) / original_time) * 100 if original_time > 0 else 0

    print("\n" + "="*50)
    print("📊 Results")
    print("="*50)
    print(f"Original (threading.local): {original_time:.4f}s")
    print(f"Optimized (Connection Pool): {optimized_time:.4f}s")

    if improvement > 5:
        print(f"Improvement: {improvement:.2f}% faster")
        print("\n✅ SIGNIFICANT PERFORMANCE GAIN")
    elif improvement >= 0:
        print(f"Improvement: {improvement:.2f}% faster")
        print("\n✅ Minor performance gain")
    else:
        print(f"Regression: {abs(improvement):.2f}% slower")
        print("\n⚠️ REGRESSION DETECTED")

if __name__ == "__main__":
    main()
