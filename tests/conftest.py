import pytest
import sys
import os

# Add the app directory to the path for all tests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

@pytest.fixture
def app():
    """Fixture to provide the FastAPI app"""
    try:
        from app.main import app
        return app
    except ImportError:
        from fastapi import FastAPI
        app = FastAPI()
        return app
