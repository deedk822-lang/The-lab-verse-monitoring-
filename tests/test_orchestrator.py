import pytest
from unittest.mock import AsyncMock
from httpx import ASGITransport, AsyncClient

# Import the FastAPI app instance and the class to be mocked
from api.server import app
from src.rainmaker_orchestrator.orchestrator import RainmakerOrchestrator

@pytest.fixture
def mock_orchestrator():
    """Fixture to create a mock instance of RainmakerOrchestrator."""
    # Use spec=True to ensure the mock has the same interface as the real class
    mock = AsyncMock(spec=RainmakerOrchestrator)
    mock.health_check.return_value = {"status": "healthy"}
    mock.execute_task.return_value = {"status": "success", "result": "Task completed."}
    return mock

@pytest.fixture
async def client(mock_orchestrator):
    """
    Create an httpx AsyncClient for testing the FastAPI app.
    This fixture manually sets the orchestrator on the app state, bypassing
    the lifespan manager for more direct and stable testing.
    """
    app.state.orchestrator = mock_orchestrator
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    # Clean up the state after the test to ensure test isolation
    if hasattr(app.state, "orchestrator"):
        del app.state.orchestrator

@pytest.mark.asyncio
async def test_health_check_healthy(client, mock_orchestrator):
    """Test the /health endpoint when the orchestrator is healthy."""
    response = await client.get("/health")

    assert response.status_code == 200
    json_response = response.json()
    assert json_response["status"] == "healthy"
    assert json_response["dependencies"]["orchestrator"]["status"] == "healthy"
    mock_orchestrator.health_check.assert_awaited_once()

@pytest.mark.asyncio
async def test_health_check_degraded(client, mock_orchestrator):
    """Test the /health endpoint when the orchestrator is degraded."""
    mock_orchestrator.health_check.return_value = {"status": "degraded", "reason": "Kimi API key not set"}

    response = await client.get("/health")

    assert response.status_code == 200
    json_response = response.json()
    assert json_response["status"] == "degraded"
    assert "Kimi API key not set" in json_response["dependencies"]["orchestrator"]["reason"]

@pytest.mark.asyncio
async def test_execute_task_success(client, mock_orchestrator):
    """Test the /execute endpoint for a successful task execution."""
    payload = {
        "type": "coding_task",
        "context": "Write a python script to print hello world.",
        "output_filename": "hello.py",
        "model": None
    }
    response = await client.post("/execute", json=payload)

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    mock_orchestrator.execute_task.assert_awaited_once_with(payload)

@pytest.mark.asyncio
async def test_execute_task_failure(client, mock_orchestrator):
    """Test the /execute endpoint for a failed task execution."""
    mock_orchestrator.execute_task.return_value = {"status": "failed", "message": "Max retries exceeded."}

    payload = {"type": "coding_task", "context": "This will fail."}
    response = await client.post("/execute", json=payload)

    assert response.status_code == 500
    assert "Max retries exceeded" in response.json()["detail"]

@pytest.mark.asyncio
async def test_execute_invalid_payload(client):
    """Test the /execute endpoint with an invalid payload (missing context)."""
    response = await client.post("/execute", json={"type": "coding_task"})

    assert response.status_code == 422
    # Check for the specific Pydantic v2 error message
    assert "Field required" in response.text
    assert "context" in response.text
