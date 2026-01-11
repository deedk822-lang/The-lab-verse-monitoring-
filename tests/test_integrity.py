# tests/test_integrity.py
import pytest
from unittest.mock import MagicMock, patch
from api.server import app
from fastapi.testclient import TestClient
from agents.background import worker

client = TestClient(app)

# 1. TEST: Verify Pydantic Model prevents crashes
@patch('api.server.HubSpot')
@patch('api.server.orchestrator')
def test_hubspot_webhook_valid(mock_orchestrator, mock_hubspot):
    # Mock the orchestrator to prevent real network calls and config access
    async def mock_call_ollama(*args, **kwargs):
        return {"message": {"content": '{"company_name": "TestCorp", "summary": "A test summary.", "intent_score": 9, "suggested_action": "Follow up."}'}}
    mock_orchestrator._call_ollama.return_value = mock_call_ollama()
    mock_orchestrator.config.get.return_value = "dummy-hubspot-token"

    # Mock the HubSpot client to prevent real API calls
    mock_hubspot.return_value = MagicMock()

    payload = {"objectId": 123, "message_body": "Test"}
    response = client.post("/webhook/hubspot", json=payload)

    assert response.status_code == 200
    assert response.json()["status"] in ["processed", "processed_with_deal_creation_error"]
    assert response.json()["contact_id"] == 123

def test_hubspot_webhook_invalid():
    # Sending string instead of int for objectId should fail gracefully (422), not crash (500)
    payload = {"objectId": "invalid_int", "message_body": "Test"}
    response = client.post("/webhook/hubspot", json=payload)
    assert response.status_code == 422

# 2. TEST: Verify Market Intel Endpoint is a Placeholder
def test_market_intel_is_structural():
    response = client.get("/intel/market?company=TestCorp")
    data = response.json()
    # Ensure we are NOT getting the hardcoded "ArcelorMittal" text
    assert "ArcelorMittal" not in str(data)
    assert data["status"] == "Integration Pending - Configure Perplexity/Google API"

# 3. TEST: Redis Rate Limit Logic (Mocked)
@patch.object(worker, 'redis_conn', new_callable=MagicMock)
def test_rate_limit_logic(mock_redis):
    # Setup mock to simulate being UNDER limit
    mock_redis.incr.return_value = 5
    assert worker.check_rate_limit("user_1") == True

    # Setup mock to simulate being OVER limit
    mock_redis.incr.return_value = 101
    assert worker.check_rate_limit("user_1") == False
