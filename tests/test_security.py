# tests/test_security.py
import pytest
from fastapi.testclient import TestClient
import hmac
import hashlib
import os
import json

from app.main import app

client = TestClient(app)

WEBHOOK_SECRET = "test-secret"

def test_webhook_security_valid_signature():
    """Test webhook with a valid signature"""
    os.environ["WEBHOOK_SECRET"] = WEBHOOK_SECRET
    test_payload = {
        "repository": {"name": "test-repo", "full_name": "test/test-repo"},
        "commit": {"hash": "abc123", "date": "2024-01-01T00:00:00Z"},
        "build_status": "SUCCESS"
    }
    body = json.dumps(test_payload).encode()
    signature = "sha256=" + hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()

    response = client.post(
        "/webhook/bitbucket",
        content=body,
        headers={"X-Hub-Signature": signature, "Content-Type": "application/json"}
    )

    assert response.status_code == 200
    del os.environ["WEBHOOK_SECRET"]

def test_webhook_security_invalid_signature():
    """Test webhook with an invalid signature"""
    os.environ["WEBHOOK_SECRET"] = WEBHOOK_SECRET
    test_payload = {
        "repository": {"name": "test-repo", "full_name": "test/test-repo"},
        "commit": {"hash": "abc123", "date": "2024-01-01T00:00:00Z"},
        "build_status": "SUCCESS"
    }
    body = json.dumps(test_payload).encode()

    response = client.post(
        "/webhook/bitbucket",
        content=body,
        headers={"X-Hub-Signature": "sha256=invalid", "Content-Type": "application/json"}
    )

    assert response.status_code == 403
    del os.environ["WEBHOOK_SECRET"]

def test_webhook_security_missing_signature():
    """Test webhook with a missing signature when a secret is configured"""
    os.environ["WEBHOOK_SECRET"] = WEBHOOK_SECRET
    test_payload = {
        "repository": {"name": "test-repo", "full_name": "test/test-repo"},
        "commit": {"hash": "abc123", "date": "2024-01-01T00:00:00Z"},
        "build_status": "SUCCESS"
    }

    response = client.post("/webhook/bitbucket", json=test_payload)

    assert response.status_code == 403
    del os.environ["WEBHOOK_SECRET"]
