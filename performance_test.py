
import time
import sys
import os
from unittest.mock import patch, MagicMock

# Ensure the script can find the vaal-ai-empire modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'vaal-ai-empire')))

from scripts.daily_automation import DailyAutomation

# Mock data for clients
MOCK_CLIENTS = [
    {"id": f"client_{i}", "name": f"Client {i}", "business_type": "butchery", "language": "afrikaans"}
    for i in range(20)
]

def benchmark_sequential(automation_instance):
    """Benchmarks the original sequential method."""
    print("\n--- Benchmarking OLD Sequential Method ---")
    start_time = time.perf_counter()

    for client in MOCK_CLIENTS:
        automation_instance._generate_for_client(client)

    end_time = time.perf_counter()
    return end_time - start_time

def benchmark_parallel(automation_instance):
    """Benchmarks the new parallelized method."""
    print("\n--- Benchmarking NEW Parallel Method ---")
    start_time = time.perf_counter()

    with patch.object(automation_instance.db, 'get_active_clients', return_value=MOCK_CLIENTS):
        automation_instance.generate_content_for_all_clients()

    end_time = time.perf_counter()
    return end_time - start_time

@patch('scripts.daily_automation.ContentScheduler')
@patch('scripts.daily_automation.ContentFactory')
@patch('scripts.daily_automation.Database')
def test_optimization(MockDatabase, MockFactory, MockScheduler):
    """Compare original vs optimized performance."""
    print("=" * 60)
    print("⚡ Bolt: Performance Comparison Test ⚡")
    print("=" * 60)
    print(f"Simulating content generation for {len(MOCK_CLIENTS)} clients...")

    # Mock the dependencies to isolate the concurrency logic
    mock_db_instance = MockDatabase.return_value
    mock_factory_instance = MockFactory.return_value
    mock_scheduler_instance = MockScheduler.return_value

    # Simulate a network delay in content generation
    def fake_generation(business_type, language):
        time.sleep(0.1)  # Simulate 100ms I/O delay
        return {"posts": ["post1", "post2"]}

    mock_factory_instance.generate_social_pack.side_effect = fake_generation
    mock_scheduler_instance.schedule_pack.return_value = None

    # Create an instance of the automation class with mocked dependencies
    automation = DailyAutomation()
    automation.db = mock_db_instance
    automation.factory = mock_factory_instance
    automation.scheduler = mock_scheduler_instance

    # --- Benchmark Sequential ---
    sequential_time = benchmark_sequential(automation)

    # --- Benchmark Parallel ---
    parallel_time = benchmark_parallel(automation)

    # --- Report Results ---
    improvement = ((sequential_time - parallel_time) / sequential_time) * 100

    print("\n" + "=" * 60)
    print("📊 RESULTS")
    print("-" * 60)
    print(f"Sequential Time: {sequential_time:.4f}s")
    print(f"Parallel Time:   {parallel_time:.4f}s")
    print("-" * 60)
    print(f"🚀 Improvement: {improvement:.2f}% faster")
    print("=" * 60)

    if improvement > 50:
        print("✅ SUCCESS: Significant performance improvement verified!")
        return True
    else:
        print("⚠️ FAILURE: No significant improvement. Optimization may not be effective.")
        return False

if __name__ == "__main__":
    success = test_optimization()
    sys.exit(0 if success else 1)
