"""Tests for api/app.py."""

import sys
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

sys.modules.setdefault("rainmaker_orchestrator", MagicMock())
sys.modules.setdefault("rainmaker_orchestrator.orchestrator", MagicMock())

TestClient = pytest.importorskip("fastapi.testclient").TestClient


def test_health_endpoint():
    with patch("api.app.RainmakerOrchestrator") as orch:
        inst = MagicMock()
        inst.aclose = AsyncMock()
        orch.return_value = inst
        from api.app import app

        client = TestClient(app)
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "healthy"}
