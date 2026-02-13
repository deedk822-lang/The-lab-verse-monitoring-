"""
Test configuration and fixtures.

Ensures tests import from correct source path.
"""

import os
from pathlib import Path
import sys

import pytest
from pytest import fixture

# FIX: Add src and root to path for tests
repo_root = Path(__file__).parent.parent
src_path = repo_root / "src"

# Add root first for app module
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

# Add src for other modules
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Verify imports work
try:
    import pr_fix_agent

    print(f"✅ Successfully imported pr_fix_agent from: {pr_fix_agent.__file__}")
except ImportError as e:
    print(f"❌ Failed to import pr_fix_agent: {e}")
    print(f"sys.path: {sys.path}")


@fixture(scope="session")
def repo_root_path():
    """Return repository root path."""
    return repo_root


@fixture(scope="session")
def src_path_fixture():
    """Return src directory path."""
    return repo_root / "src"


@pytest.fixture(scope="session", autouse=True)
def configure_env():
    """Set required environment variables for tests."""
    os.environ.setdefault("REDIS_URL", "redis://localhost:6380/0")
    os.environ.setdefault("JWT_SECRET", "test-secret")
    os.environ.setdefault(
        "OIDC_DISCOVERY",
        "https://example.com/.well-known/openid-configuration",
    )
    os.environ.setdefault("KIMI_API_KEY", "")

    yield


@pytest.fixture
def client():
    """Fixture to provide the test client"""
    from fastapi.testclient import TestClient

    from app.main import app

    return TestClient(app)
