# tests/test_integrity.py
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import json
from api.server import app
from fastapi.testclient import TestClient
from agents.background import worker

client = TestClient(app)

# 1. TEST: Verify Pydantic Model prevents crashes
@patch('api.server.RainmakerOrchestrator')
@patch('api.server.HubSpot')
@pytest.mark.asyncio
async def test_hubspot_webhook_valid(mock_hubspot, mock_rainmaker_orchestrator):
    # Mock the instance that will be created inside the lifespan manager
    """
 coderabbitai/docstrings/52d56b6
    Verify the HubSpot webhook processes a valid payload and returns a processed status with the original contact ID.
    
    Posts a payload with `objectId` 123 to `/webhook/hubspot` and asserts the response has HTTP 200, the `status` is either "processed" or "processed_with_deal_creation_error", and `contact_id` equals 123.
    """
    async def mock_call_ollama(*args, **kwargs):
        """
        Simulates an Ollama API call by returning a fixed response payload containing company analysis.
        
        Returns:
            dict: A response dictionary with a "message" key whose "content" is a JSON string:
                - "company_name" (str): "TestCorp"
                - "summary" (str): "A test summary."
                - "intent_score" (int): 9
                - "suggested_action" (str): "Follow up."
        """
        return {"message": {"content": '{"company_name": "TestCorp", "summary": "A test summary.", "intent_score": 9, "suggested_action": "Follow up."}'}}
    mock_orchestrator._call_ollama.return_value = mock_call_ollama()
    mock_orchestrator.config.get.return_value = "dummy-hubspot-token"

    Verifies that a valid HubSpot webhook payload is accepted and returns the expected accepted status and contact ID.
    
    Sets up mocked RainmakerOrchestrator (including a stubbed async Ollama response) and a mocked HubSpot client, posts a payload to /webhook/hubspot, and asserts the response status code is 200 with JSON {"status": "accepted", "contact_id": 123}.
    """
    mock_orchestrator_instance = mock_rainmaker_orchestrator.return_value
    mock_orchestrator_instance.config = {'HUBSPOT_ACCESS_TOKEN': 'fake-token'}
    
    # Mock orchestrator's async Ollama call
    mock_orchestrator_instance._call_ollama = AsyncMock(return_value={
        "message": {
            "content": json.dumps({
                "company_name": "TestCorp",
                "summary": "This is a test summary.",
                "intent_score": 9,
                "suggested_action": "Follow up immediately."
            })
        }
    })
 main

    # Mock the HubSpot client to prevent real API calls
    mock_hubspot.return_value = MagicMock()

    payload = {"objectId": 123, "message_body": "Test"}
    response = client.post("/webhook/hubspot", json=payload)

    assert response.status_code == 200
    assert response.json() == {"status": "accepted", "contact_id": 123}

def test_hubspot_webhook_invalid():
    # Sending string instead of int for objectId should fail gracefully (422), not crash (500)
    payload = {"objectId": "invalid_int", "message_body": "Test"}
    response = client.post("/webhook/hubspot", json=payload)
    assert response.status_code == 422

# 2. TEST: Verify Market Intel Endpoint is a Placeholder
def test_market_intel_is_structural():
    """
    Verify the market intelligence endpoint returns a structural placeholder response rather than the hardcoded "ArcelorMittal".
    
    Asserts that the JSON response for GET /intel/market?company=TestCorp does not contain the string "ArcelorMittal" and that the "status" field equals "Integration Pending - Configure Perplexity/Google API".
    """
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