import pytest
from aiohttp import web
from src.kimi_instruct.core import KimiInstruct
from src.kimi_instruct.service import handle_status, handle_create_task, handle_health, default_serializer
import json

# This fixture sets up the test client for the Kimi service
@pytest.fixture
def kimi_client(aiohttp_client):
    app = web.Application()
    app['kimi'] = KimiInstruct()
    app.router.add_get("/status", handle_status)
    app.router.add_post("/tasks", handle_create_task)
    app.router.add_get("/health", handle_health)

    # The default JSON serializer needs to be passed to the client
    return aiohttp_client(app, server_kwargs={'port': 8084})

async def test_health_endpoint(kimi_client):
    """Tests if the /health endpoint is working."""
    client = await kimi_client
    resp = await client.get("/health")
    assert resp.status == 200
    data = await resp.json()
    assert data == {"status": "healthy"}

async def test_status_endpoint(kimi_client):
    """Tests the /status endpoint for initial state."""
    client = await kimi_client
    resp = await client.get("/status")
    assert resp.status == 200
    data = await resp.json()
    assert "project_context" in data
    assert "task_summary" in data
    assert data["task_summary"]["total"] == 0

async def test_create_task_endpoint(kimi_client):
    """Tests creating a task and then verifying it via the status endpoint."""
    client = await kimi_client
    payload = {
        "title": "Integration Test Task",
        "description": "This is a test task created via the API.",
        "priority": "high"
    }
    resp = await client.post("/tasks", json=payload)
    assert resp.status == 201, f"Expected status 201, but got {resp.status}"
    data = await resp.json()
    assert "task_id" in data

    # Now, check the status to see if the task is registered
    status_resp = await client.get("/status")
    assert status_resp.status == 200
    status_data = await status_resp.json()
    assert status_data["task_summary"]["total"] == 1

async def test_create_task_invalid_payload(kimi_client):
    """Tests that creating a task with a missing title returns a 400 error."""
    client = await kimi_client
    payload = {"description": "This payload is missing a title."}
    resp = await client.post("/tasks", json=payload)
    assert resp.status == 400
    data = await resp.json()
    assert "error" in data
    assert "title" in data["error"].lower()