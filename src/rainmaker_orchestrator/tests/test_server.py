from unittest.mock import AsyncMock, Mock
import pytest
from api.app import app

@pytest.mark.asyncio
async def test_health_check_healthy(client, monkeypatch):
    """Test health check with healthy Kimi client."""

    # Create mock with async health_check method
    mock_kimi = AsyncMock(return_value={"status": "healthy"})

    # Patch app state
    monkeypatch.setattr(app.state.orchestrator, "_call_kimi", mock_kimi)

    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"