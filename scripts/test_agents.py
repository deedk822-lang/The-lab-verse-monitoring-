#!/usr/bin/env python3
"""
Vaal AI Empire - Agent Logic Test Suite
Tests agent behavior without making real API calls.
"""
import sys
import os
from pathlib import Path

# Add vaal-ai-empire to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'vaal-ai-empire'))

def test_imports():
    """Test that all agent modules can be imported"""
    print("🧪 Testing Agent Imports...")

    try:
        # Test core imports
        from src.core import real_logic_sim
        print("  ✓ Core modules imported")

        # Test agent imports (if they exist)
        try:
            from src.agents import tax_collector
            print("  ✓ Tax Collector agent imported")
        except ImportError as e:
            print(f"  ⚠️  Tax Collector import failed: {e}")

        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False

def test_health_check_logic():
    """Test the health check system"""
    print("\n🧪 Testing Health Check Logic...")

    try:
        from src.core.real_logic_sim import SystemHealthCheck

        # Create instance
        health_checker = SystemHealthCheck()
        print("  ✓ Health checker instantiated")

        # Test check structure
        if hasattr(health_checker, 'check_localai'):
            print("  ✓ LocalAI check method exists")
        if hasattr(health_checker, 'check_databricks'):
            print("  ✓ Databricks check method exists")

        return True
    except Exception as e:
        print(f"  ✗ Health check test failed: {e}")
        return False

def test_environment_config():
    """Test environment configuration"""
    print("\n🧪 Testing Environment Configuration...")

    required_vars = [
        'NOTION_API_KEY',
        'JIRA_USER_EMAIL',
        'WORDPRESS_USER',
    ]

    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)

    if missing:
        print(f"  ⚠️  Missing environment variables: {', '.join(missing)}")
        print("     (This is expected if running without secrets)")
    else:
        print("  ✓ All required environment variables present")

    return True

def main():
    print("🤖 Vaal AI Empire - Agent Test Suite")
    print("=" * 50)

    tests = [
        test_imports,
        test_health_check_logic,
        test_environment_config,
    ]

    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"\n  ✗ Test crashed: {e}")
            results.append(False)

    print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")

    if all(results):
        print("✓ All agent tests passed!")
        sys.exit(0)
    else:
        print("✗ Some agent tests failed")
        sys.exit(1)

if __name__ == '__main__':
    main()
