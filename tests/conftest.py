<<<<<<< HEAD
"""
Test configuration and fixtures.

FIX: Ensures tests import from correct source path.
"""

import sys
from pathlib import Path
=======
import os
import sys

import pytest
>>>>>>> main

# FIX: Add src to path for tests
repo_root = Path(__file__).parent.parent
src_path = repo_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

<<<<<<< HEAD
# Verify imports work
try:
    import pr_fix_agent
    print(f"✅ Successfully imported pr_fix_agent from: {pr_fix_agent.__file__}")
except ImportError as e:
    print(f"❌ Failed to import pr_fix_agent: {e}")
    print(f"sys.path: {sys.path}")
    raise

import pytest
from pytest import fixture


@fixture(scope="session")
def repo_root_path():
    """Return repository root path."""
    return repo_root


@fixture(scope="session")
def src_path():
    """Return src directory path."""
    return repo_root / "src"
=======
@pytest.fixture
def client():
    """Fixture to provide the test client"""
    from fastapi.testclient import TestClient

    from app.main import app
    return TestClient(app)
>>>>>>> main
