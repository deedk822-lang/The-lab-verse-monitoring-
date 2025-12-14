import pytest
from fastapi.testclient import TestClient
import numpy as np
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.anomaly_detection.main import app

@pytest.fixture(scope="function")
def client():
    """
    A fixture that provides a test client for the FastAPI app,
    and handles the lifespan events correctly.
    """
    os.environ['PYTEST_RUNNING'] = 'true'
    with TestClient(app) as c:
        yield c
    del os.environ['PYTEST_RUNNING']

def test_health_check(client):
    """Tests if the /health endpoint is working."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_detect_timeseries_anomalies_lstm(client):
    """Tests the /detect/timeseries endpoint with the LSTM model."""
    sequences = np.random.rand(5, 10, 1).tolist()
    payload = {"sequences": sequences, "model": "lstm"}
    response = client.post("/detect/timeseries", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "anomalies" in data
    if data["anomalies"]:
        assert "sequence_index" in data["anomalies"][0]
        assert "reconstruction_error" in data["anomalies"][0]

def test_detect_multi_cloud_anomalies(client):
    """Tests the /detect/multi-cloud endpoint."""
    payload = {"time_window_hours": 12}
    response = client.post("/detect/multi-cloud", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "multi_cloud_anomalies" in data
    assert "cross_cloud_patterns" in data
    assert "aws" in data["multi_cloud_anomalies"]
    assert "cost_anomalies" in data["multi_cloud_anomalies"]["aws"]

def test_explain_anomaly(client):
    """Tests the /explain endpoint."""
    sample = np.random.rand(10, 1).tolist()
    payload = {"sample": sample, "context": {"metric_name": "test_metric"}}
    response = client.post("/explain", json=payload)
    assert response.status_code == 503
    data = response.json()
    assert "detail" in data
    assert "not available" in data["detail"]

def test_trigger_alert(client):
    """Tests the /alert endpoint."""
    payload = {
        "alert_id": "integration-test-alert",
        "title": "Test Alert",
        "description": "This is an integration test alert.",
        "severity": "critical",
        "channels": ["slack"],
        "anomaly_data": {"metric": "cpu_usage", "value": 0.99}
    }
    response = client.post("/alert", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "sent"
    assert "slack" in data["channels"]