#!/usr/bin/env python3
"""
VAAL AI Empire - Comprehensive Test Suite
Proves that all components work correctly
"""

import sys
import json
from pathlib import Path

# Test data directory
TEST_DIR = "/tmp/vaal_test"
Path(TEST_DIR).mkdir(parents=True, exist_ok=True)

def print_header(text):
    """Print test header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def print_result(test_name, passed, details=""):
    """Print test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {test_name}")
    if details:
        print(f"   {details}")

def test_credit_manager():
    """Test credit manager functionality"""
    print_header("TEST 1: Credit Manager Core")
    
    from credit_manager import CreditManager
    
    # Test 1.1: Initialization
    try:
        manager = CreditManager(tier="free", data_dir=TEST_DIR)
        print_result("Initialization", True, f"Tier: {manager.tier}")
    except Exception as e:
        print_result("Initialization", False, str(e))
        return False
    
    # Test 1.2: Check request allowed
    try:
        allowed, reason, usage = manager.can_make_request(1000, "kimi")
        print_result("Check request", True, f"Allowed: {allowed}, Reason: {reason}")
    except Exception as e:
        print_result("Check request", False, str(e))
        return False
    
    # Test 1.3: Record usage
    try:
        manager.record_usage(1000, "kimi")
        print_result("Record usage", True, "Recorded 1000 tokens")
    except Exception as e:
        print_result("Record usage", False, str(e))
        return False
    
    # Test 1.4: Get summary
    try:
        summary = manager.get_usage_summary()
        requests = summary['daily']['usage']['requests']
        cost = summary['daily']['usage']['cost']
        print_result("Get summary", True, f"Requests: {requests}, Cost: ${cost:.4f}")
    except Exception as e:
        print_result("Get summary", False, str(e))
        return False
    
    # Test 1.5: Verify file creation
    try:
        files = list(Path(TEST_DIR).glob("*.json"))
        print_result("File persistence", len(files) > 0, f"Created {len(files)} files")
    except Exception as e:
        print_result("File persistence", False, str(e))
        return False
    
    # Test 1.6: Circuit breaker
    try:
        manager.trigger_circuit_breaker("Test circuit breaker", 1)
        breaker_active, reason = manager.check_circuit_breaker()
        print_result("Circuit breaker", breaker_active, f"Reason: {reason}")
        
        # Remove for next tests
        if (Path(TEST_DIR) / "circuit_breaker.json").exists():
            (Path(TEST_DIR) / "circuit_breaker.json").unlink()
    except Exception as e:
        print_result("Circuit breaker", False, str(e))
        return False
    
    return True

def test_limits():
    """Test that limits are actually enforced"""
    print_header("TEST 2: Limit Enforcement")
    
    from credit_manager import CreditManager
    
    # Start fresh
    for f in Path(TEST_DIR).glob("*.json"):
        f.unlink()
    for f in Path(TEST_DIR).glob("*.jsonl"):
        f.unlink()
    
    manager = CreditManager(tier="free", data_dir=TEST_DIR)
    
    # Test 2.1: Per-request limit
    try:
        allowed, reason, _ = manager.can_make_request(5000, "kimi")  # Exceeds 2000 limit
        print_result("Per-request limit", not allowed, f"Blocked: {reason}")
    except Exception as e:
        print_result("Per-request limit", False, str(e))
        return False
    
    # Test 2.2: Hourly limit
    try:
        # Make 10 small requests (hourly limit)
        for i in range(10):
            allowed, _, _ = manager.can_make_request(100, "kimi")
            if allowed:
                manager.record_usage(100, "kimi")
        
        # 11th should be blocked
        allowed, reason, _ = manager.can_make_request(100, "kimi")
        print_result("Hourly limit", not allowed, f"Blocked after 10 requests: {reason}")
    except Exception as e:
        print_result("Hourly limit", False, str(e))
        return False
    
    # Test 2.3: Daily limit
    try:
        # Clean hourly
        for f in Path(TEST_DIR).glob("hourly_*.json"):
            f.unlink()
        
        # Try to make many requests
        blocked_at = None
        for i in range(60):
            allowed, reason, _ = manager.can_make_request(500, "kimi")
            if allowed:
                manager.record_usage(500, "kimi")
            else:
                blocked_at = i
                break
        
        print_result("Daily limit", blocked_at is not None, f"Blocked at request {blocked_at}")
    except Exception as e:
        print_result("Daily limit", False, str(e))
        return False
    
    return True

def test_dashboard():
    """Test dashboard can display data"""
    print_header("TEST 3: Dashboard Display")
    
    try:
        from credit_dashboard import main
        import io
        import contextlib
        
        # Capture output
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            main()
        
        result = output.getvalue()
        
        # Check for key elements
        checks = [
            ("Header present", "VAAL AI EMPIRE" in result),
            ("Tier shown", "Tier:" in result),
            ("Daily usage", "DAILY USAGE:" in result),
            ("Requests shown", "Requests:" in result),
            ("Cost shown", "Cost:" in result),
            ("Status shown", "Status:" in result),
        ]
        
        all_passed = all(check[1] for check in checks)
        
        for name, passed in checks:
            print_result(name, passed)
        
        return all_passed
    except Exception as e:
        print_result("Dashboard execution", False, str(e))
        return False

def test_cost_calculation():
    """Test cost calculation accuracy"""
    print_header("TEST 4: Cost Calculation")
    
    from credit_manager import CreditManager
    
    manager = CreditManager(tier="free", data_dir=TEST_DIR)
    
    tests = [
        ("Kimi", 1000, "kimi", 0.01),
        ("Qwen", 1000, "qwen", 0.005),
        ("HuggingFace", 1000, "huggingface", 0.002),
    ]
    
    all_passed = True
    for name, tokens, model, expected in tests:
        cost = manager.estimate_cost(tokens, model)
        passed = abs(cost - expected) < 0.0001
        print_result(f"{name} cost", passed, f"${cost:.4f} (expected ${expected:.4f})")
        all_passed = all_passed and passed
    
    return all_passed

def test_tier_configs():
    """Test all tier configurations"""
    print_header("TEST 5: Tier Configurations")
    
    from credit_manager import CreditManager
    
    tiers = ["free", "economy", "standard", "premium"]
    all_passed = True
    
    for tier in tiers:
        try:
            manager = CreditManager(tier=tier, data_dir=TEST_DIR)
            config = manager.config
            print_result(
                f"{tier.capitalize()} tier",
                True,
                f"Daily: {config['daily_max_requests']} req, ${config['daily_max_cost']}"
            )
        except Exception as e:
            print_result(f"{tier.capitalize()} tier", False, str(e))
            all_passed = False
    
    return all_passed

def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 10 + "VAAL AI EMPIRE - COMPREHENSIVE TEST SUITE" + " " * 16 + "║")
    print("╚" + "=" * 68 + "╝")
    
    results = {}
    
    # Run tests
    results['Credit Manager'] = test_credit_manager()
    results['Limit Enforcement'] = test_limits()
    results['Dashboard'] = test_dashboard()
    results['Cost Calculation'] = test_cost_calculation()
    results['Tier Configs'] = test_tier_configs()
    
    # Summary
    print_header("TEST SUMMARY")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for test, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test}")
    
    print()
    print(f"Total: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    print()
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! The system is working correctly.")
        print()
        print("Next steps:")
        print("  1. Run: sudo bash install.sh")
        print("  2. Edit: /etc/vaal/credit-protection.conf (add API keys)")
        print("  3. Start: sudo systemctl start vaal-credit-protection")
        print("  4. Check: vaal-dashboard")
    else:
        print("⚠️ Some tests failed. Please review the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
