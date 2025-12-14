import timeit
import os
import sys
import sqlite3
from contextlib import contextmanager

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.database import Database

# --- Test Configuration ---
LEGACY_DB_PATH = "legacy_benchmark.db"
OPTIMIZED_DB_PATH = "optimized_benchmark.db"
ITERATIONS = 1000

class LegacyDatabase:
    """
    A recreation of the original, inefficient database class that creates a new
    connection for every query.
    """
    def __init__(self, db_path):
        self.db_path = db_path
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.init_database()

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def init_database(self):
        with self.get_connection() as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY, name TEXT)")
            conn.execute("INSERT INTO test (id, name) VALUES (1, 'test_data')")
            conn.commit()

    def get_test_data(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM test WHERE id = 1")
            return cursor.fetchone()

def cleanup_files():
    """Remove the temporary database files."""
    if os.path.exists(LEGACY_DB_PATH):
        os.remove(LEGACY_DB_PATH)
    if os.path.exists(OPTIMIZED_DB_PATH):
        os.remove(OPTIMIZED_DB_PATH)

def benchmark_performance():
    """
    Benchmarks the performance of the optimized database class against the legacy
    connection-per-query class.
    """
    # Ensure a clean state
    cleanup_files()

    try:
        # Benchmark the legacy database
        legacy_db = LegacyDatabase(db_path=LEGACY_DB_PATH)
        legacy_time = timeit.timeit(legacy_db.get_test_data, number=ITERATIONS)

        # Benchmark the optimized database
        # We create a separate file to be fair
        if os.path.exists(OPTIMIZED_DB_PATH):
            os.remove(OPTIMIZED_DB_PATH)
        optimized_db = Database(db_path=OPTIMIZED_DB_PATH)

        with optimized_db.get_cursor() as cursor:
            cursor.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY, name TEXT)")
            cursor.execute("INSERT INTO test (id, name) VALUES (1, 'test_data')")

        def optimized_query():
            conn = optimized_db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM test WHERE id = 1")
            return cursor.fetchone()

        optimized_time = timeit.timeit(optimized_query, number=ITERATIONS)
        optimized_db.close_connection() # Manually close for cleanup

        # Calculate and print the performance improvement
        improvement = ((legacy_time - optimized_time) / legacy_time) * 100 if legacy_time > 0 else float('inf')

        print("--- Database Performance Benchmark ---")
        print(f"Legacy (connection-per-query): {legacy_time:.4f} seconds for {ITERATIONS} queries.")
        print(f"Optimized (connection pooling): {optimized_time:.4f} seconds for {ITERATIONS} queries.")
        print(f"Performance Improvement: {improvement:.2f}%")
        print("------------------------------------")

        if improvement > 90:
            print("✅ Performance benchmark passed. The optimization is highly effective.")
            return True
        else:
            print(f"⚠️ Performance benchmark warning. Improvement of {improvement:.2f}% is less than the 90% target.")
            return False

    finally:
        # Final cleanup
        cleanup_files()

if __name__ == "__main__":
    if benchmark_performance():
        sys.exit(0)
    else:
        sys.exit(1)
