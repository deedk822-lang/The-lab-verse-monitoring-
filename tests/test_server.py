import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock

from api.server import app
from src.rainmaker_orchestrator.orchestrator import RainmakerOrchestrator
from src.rainmaker_orchestrator.clients.kimi import KimiApiClient

@pytest.fixture
def mock_orchestrator():
    mock = AsyncMock(spec=RainmakerOrchestrator)
    mock.health_check.return_value = {"status": "healthy"}
    mock.execute_task.return_value = {"status": "success"}
    return mock

@pytest.fixture
def mock_kimi_client():
    mock = AsyncMock(spec=KimiApiClient)
    mock.health_check.return_value = {"status": "healthy"}
    return mock

@pytest.fixture
async def client(mock_orchestrator, mock_kimi_client):
    app.state.orchestrator = mock_orchestrator
    app.state.kimi_client = mock_kimi_client
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    del app.state.orchestrator
    del app.state.kimi_client

@pytest.mark.asyncio
async def test_health_check_healthy(client, mock_orchestrator, mock_kimi_client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    mock_orchestrator.health_check.assert_awaited_once()
    mock_kimi_client.health_check.assert_awaited_once()

@pytest.mark.asyncio
async def test_execute_task_success(client, mock_orchestrator):
    payload = {"context": "test"}
    response = await client.post("/execute", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    mock_orchestrator.execute_task.assert_awaited_once()
