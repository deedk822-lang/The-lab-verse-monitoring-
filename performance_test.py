# performance_test.py
import time
import sys
from unittest.mock import MagicMock, patch

# To allow the test to run without installing the agent, we add it to the path
sys.path.insert(0, ".")

# --- Original (Sequential) Implementation ---
def original_discover_services(creds):
    """The original, sequential implementation for benchmarking."""
    from googleapiclient.discovery import build
    services = {}
    time.sleep(0.1) # Simulate network latency
    try:
        gmail = build("gmail", "v1", credentials=creds)
        gmail.users().getProfile(userId="me").execute()
        services["Gmail"] = True
    except Exception:
        services["Gmail"] = False
    time.sleep(0.1)
    try:
        gbp = build("mybusinessbusinessinformation", "v1", credentials=creds)
        accounts = gbp.accounts().list().execute()
        services["GoogleBusiness"] = bool(accounts.get("accounts"))
    except Exception:
        services["GoogleBusiness"] = False
    time.sleep(0.1)
    try:
        yt = build("youtube", "v3", credentials=creds)
        yt.channels().list(mine=True, part="id").execute()
        services["YouTube"] = True
    except Exception:
        services["YouTube"] = False
    time.sleep(0.1)
    try:
        cal = build("calendar", "v3", credentials=creds)
        cal.calendarList().list(maxResults=1).execute()
        services["Calendar"] = True
    except Exception:
        services["Calendar"] = False
    return services

# --- Optimized (Concurrent) Implementation ---
# We import the function from the agent that we modified
from agent import _discover_services as optimized_discover_services

def benchmark_function(func, creds):
    """Benchmark a function."""
    start = time.perf_counter()
    func(creds)
    end = time.perf_counter()
    return end - start

def test_optimization():
    """Compare original vs optimized performance."""
    print("=" * 60)
    print("⚡ Bolt Performance Test: Concurrent Service Discovery ⚡")
    print("=" * 60)

    mock_creds = MagicMock()

    # Mock the googleapiclient.discovery.build function
    with patch('googleapiclient.discovery.build') as mock_build:
        # Configure the mock to return a mock service object
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        # Test correctness first
        original_result = original_discover_services(mock_creds)

        # Define a side effect that simulates latency and returns a mock
        def mock_execute_with_latency(*args, **kwargs):
            time.sleep(0.1)
            # Return a new MagicMock to mimic the API returning an object
            return MagicMock()

        # Apply the side effect to all execute calls for the optimized function
        mock_service.users.return_value.getProfile.return_value.execute.side_effect = mock_execute_with_latency
        mock_service.accounts.return_value.list.return_value.execute.side_effect = mock_execute_with_latency
        mock_service.channels.return_value.list.return_value.execute.side_effect = mock_execute_with_latency
        mock_service.calendarList.return_value.list.return_value.execute.side_effect = mock_execute_with_latency

        optimized_result = optimized_discover_services(mock_creds)

        # Sort the results to ensure they are comparable
        original_sorted = sorted(original_result.items())
        optimized_sorted = sorted(optimized_result.items())

        assert original_sorted == optimized_sorted, "Results don't match!"
        print("✅ Correctness verified: Results match")

        # Benchmark speed
        original_time = benchmark_function(original_discover_services, mock_creds)
        optimized_time = benchmark_function(optimized_discover_services, mock_creds)

        improvement = ((original_time - optimized_time) / original_time) * 100

        print(f"\nOriginal (Sequential): {original_time:.4f}s")
        print(f"Optimized (Concurrent): {optimized_time:.4f}s")
        print(f"Improvement: {improvement:.1f}% faster")

        if improvement > 50:
            print("✅ SIGNIFICANT IMPROVEMENT")
        elif improvement > 0:
            print("✅ Minor improvement")
        else:
            print("⚠️ NO IMPROVEMENT - Optimization may not be effective")

        return improvement > 0

if __name__ == "__main__":
    success = test_optimization()
    sys.exit(0 if success else 1)
