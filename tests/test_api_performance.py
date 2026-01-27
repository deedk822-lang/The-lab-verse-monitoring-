import asyncio
import time
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.server import app

client = TestClient(app)

@pytest.mark.asyncio
async def test_execute_endpoint_performance():
    """
    Tests that the /execute endpoint responds in under 1 second.
    """
    with patch("api.server.RainmakerOrchestrator") as mock_orchestrator:
        mock_instance = MagicMock()
        mock_instance.execute_task = MagicMock()
        mock_orchestrator.return_value = mock_instance

        start_time = time.time()
        response = client.post(
            "/execute",
            json={"type": "coding_task", "context": "test", "output_filename": "test.py"},
        )
        end_time = time.time()

        assert response.status_code == 200
        assert response.json() == {"status": "accepted", "message": "Task queued for execution."}
        assert (end_time - start_time) < 1.0
