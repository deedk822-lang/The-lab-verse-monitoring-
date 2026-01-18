import pytest
from fastapi.testclient import TestClient
from api.app import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c
