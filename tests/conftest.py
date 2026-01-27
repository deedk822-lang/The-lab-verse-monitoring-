import pytest
import sys
import os

# Add the app directory to the path for all tests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

@pytest.fixture
def client():
    """Fixture to provide the test client"""
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)
