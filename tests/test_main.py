import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.main import app
import app.main as app_main

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
    assert response.status_code == 200 # Asserts that a valid payload should result in 200


def _atlassian_payload():
    return {
        "event": "build_status",
        "date": "2026-01-01T00:00:00Z",
        "actor": {"name": "tester"},
        "repository": {"name": "test-repo"},
        "commit": {"hash": "abc123", "date": "2026-01-01T00:00:00Z"},
        "build_status": {"state": "FAILED"},
    }


def test_atlassian_webhook_requires_header(monkeypatch):
    app_main._seen_ids.clear()
    monkeypatch.setenv("SELF_HEALING_KEY", "a" * 64)

    response = client.post("/webhook/atlassian", json=_atlassian_payload())
    assert response.status_code == 401


def test_atlassian_webhook_accepts_valid_header(monkeypatch):
    app_main._seen_ids.clear()
    monkeypatch.setenv("SELF_HEALING_KEY", "a" * 64)

    response = client.post(
        "/webhook/atlassian",
        json=_atlassian_payload(),
        headers={"SELF_HEALING_KEY": "a" * 64, "X-Atlassian-Webhook-Identifier": "evt-1"},
    )
    assert response.status_code == 200


def test_atlassian_webhook_dedupes(monkeypatch):
    app_main._seen_ids.clear()
    monkeypatch.setenv("SELF_HEALING_KEY", "a" * 64)

    headers = {"SELF_HEALING_KEY": "a" * 64, "X-Atlassian-Webhook-Identifier": "evt-dup"}

    r1 = client.post("/webhook/atlassian", json=_atlassian_payload(), headers=headers)
    assert r1.status_code == 200

    r2 = client.post("/webhook/atlassian", json=_atlassian_payload(), headers=headers)
    assert r2.status_code == 200
    assert r2.json().get("status") == "ignored_duplicate"


@pytest.mark.asyncio
async def test_async_functionality():
    """Test async functionality"""
    assert True

def test_bitbucket_webhook_invalid_payload():
    '''Test Bitbucket webhook with an invalid payload for validation failure'''
    invalid_payload = {
        "repository": {"name": "test-repo"},
        "commit": {"hash": "abc123", "date": "2024-01-01T00:00:00Z"},
        # Missing 'build_status' to make it invalid
    }
    response = client.post("/webhook/bitbucket", json=invalid_payload)
    assert response.status_code == 422 # Asserts validation failure for invalid payload
