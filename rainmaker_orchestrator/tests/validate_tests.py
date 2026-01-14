"""
Quick validation script to check that all test files can be imported.
Run this before committing to catch import errors early.
"""
import sys
from pathlib import Path

def validate_test_imports():
    """Validate that all test files can be imported."""
    test_files = [
        'test_healer',
        'test_kimi_client',
        'test_core_orchestrator',
        'test_config',
    ]

    print("Validating test file imports...")
    print("=" * 50)

    failed = []
    for test_file in test_files:
        try:
            __import__(test_file)
            print(f"✅ {test_file}.py - OK")
        except Exception as e:
            print(f"❌ {test_file}.py - FAILED: {e}")
            failed.append((test_file, e))

    print("=" * 50)

    if failed:
        print(f"\n❌ {len(failed)} test file(s) failed to import:")
        for test_file, error in failed:
            print(f"   - {test_file}: {error}")
        return False
    else:
        print(f"\n✅ All {len(test_files)} test files imported successfully!")
        return True

if __name__ == "__main__":
    # Add parent directories to path
    test_dir = Path(__file__).parent
    sys.path.insert(0, str(test_dir))
    sys.path.insert(0, str(test_dir.parent))

    success = validate_test_imports()
    sys.exit(0 if success else 1)