import pytest
from unittest.mock import AsyncMock, MagicMock
from agents.healer import SelfHealingAgent

@pytest.fixture
def mock_kimi_client():
    """
    Create a mock Kimi client with an asynchronous `generate_hotfix` method for use in tests.
    
    Returns:
        MagicMock: A MagicMock instance with `generate_hotfix` set to an AsyncMock.
    """
    client = MagicMock()
    client.generate_hotfix = AsyncMock()
    return client

@pytest.fixture
def valid_alert():
    """
    Provide a sample alert payload representing a firing HighCPU alert.
    
    Returns:
        dict: Alert dictionary with keys:
            - status: "firing"
            - labels: contains "alertname": "HighCPU"
            - annotations: contains "summary" and "description"
            - startsAt: ISO-8601 start timestamp
            - endsAt: ISO-8601 end timestamp
            - generatorURL: source URL for the alert
    """
    return {
        "status": "firing",
        "labels": {"alertname": "HighCPU"},
        "annotations": {"summary": "CPU usage is high", "description": "The CPU usage is over 90% for 5 minutes."},
        "startsAt": "2025-01-01T00:00:00Z",
        "endsAt": "2025-01-01T01:00:00Z",
        "generatorURL": "http://prometheus.example.com"
    }

@pytest.mark.asyncio
async def test_process_alert_success(mock_kimi_client, valid_alert):
    mock_kimi_client.generate_hotfix.return_value = '{"file_path": "app.js", "code_patch": "console.log(\'fixed\');", "description": "A fix"}'

    agent = SelfHealingAgent(kimi_client=mock_kimi_client)
    result = await agent.process_alert(valid_alert)

    assert "blueprint" in result
    assert result["blueprint"]["file_path"] == "app.js"
    assert result["confidence"] > 0
    assert "estimated_impact" in result

@pytest.mark.asyncio
async def test_process_alert_invalid_format(mock_kimi_client):
    agent = SelfHealingAgent(kimi_client=mock_kimi_client)

    with pytest.raises(ValueError, match="Invalid alert format"):
        await agent.process_alert({"invalid": "alert"})

@pytest.mark.asyncio
async def test_process_alert_invalid_blueprint(mock_kimi_client, valid_alert):
    mock_kimi_client.generate_hotfix.return_value = '{"file_path": "app.js"}' # Missing fields

    agent = SelfHealingAgent(kimi_client=mock_kimi_client)

    with pytest.raises(ValueError, match="Invalid blueprint generated"):
        await agent.process_alert(valid_alert)