"""Tests for api/server.py."""

import sys
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

sys.modules.setdefault("rainmaker_orchestrator", MagicMock())
sys.modules.setdefault("rainmaker_orchestrator.orchestrator", MagicMock())
sys.modules.setdefault("openlit", MagicMock())

TestClient = pytest.importorskip("fastapi.testclient").TestClient


def test_health_endpoint():
    with patch("api.server.RainmakerOrchestrator") as orch:
        orch.return_value.aclose = AsyncMock()
        from api.server import app

        with TestClient(app) as client:
            resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "connected"


def test_execute_success():
    orchestrator = MagicMock()
    orchestrator.aclose = AsyncMock()
    orchestrator.execute_task = AsyncMock(return_value={"status": "ok"})

    with patch("api.server.RainmakerOrchestrator", return_value=orchestrator):
        from api.server import app

        with TestClient(app) as client:
            resp = client.post("/execute", json={"type": "authority_task", "context": "run"})
            assert resp.status_code == 200
            assert resp.json()["status"] == "ok"
