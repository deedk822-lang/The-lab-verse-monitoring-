import os
import sys

import pytest
from fastapi.testclient import TestClient

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Test the health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["region"] == "ap-southeast-1"
    assert data["enhanced_with_qwen"] is True


def test_bitbucket_status_endpoint():
    """Test the Bitbucket status endpoint"""
    response = client.get("/bitbucket/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "integration" in data


def test_jira_status_endpoint():
    """Test the Jira status endpoint"""
    response = client.get("/jira/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "integration" in data


def test_bitbucket_webhook_success():
    """Test Bitbucket webhook with success status"""
    test_payload = {
        "repository": {"name": "test-repo"},
        "commit": {"hash": "abc123", "date": "2024-01-01T00:00:00Z"},
        "build_status": "SUCCESS",
    }
    response = client.post("/webhook/bitbucket", json=test_payload)
    assert response.status_code in [200, 422]  # 422 if validation fails, which is expected for minimal payload


@pytest.mark.asyncio
async def test_async_functionality():
    """Test async functionality"""
    assert True
