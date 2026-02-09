"""Tests for app/metrics.py."""

import importlib
import pytest


prom = pytest.importorskip("prometheus_client")
pytest.importorskip("fastapi")


@pytest.fixture
def metrics_module(monkeypatch):
    import sys
    from unittest.mock import MagicMock

    monkeypatch.setitem(sys.modules, "pynvml", MagicMock())
    mod = importlib.import_module("app.metrics")
    return mod


def test_metric_definitions_exist(metrics_module):
    assert metrics_module.http_requests_total is not None
    assert metrics_module.llm_requests_total is not None
    assert metrics_module.security_events_total is not None


def test_track_time_sync(metrics_module):
    metric = prom.Histogram("test_sync_duration_seconds", "test")

    @metrics_module.track_time(metric)
    def _fn():
        return "ok"

    assert _fn() == "ok"


def test_track_llm_request_context(metrics_module):
    with metrics_module.track_llm_request("openai", "gpt-4", "chat"):
        pass


def test_metrics_endpoint_response(metrics_module):
    resp = metrics_module.metrics_endpoint()
    assert resp is not None
    assert resp.media_type == prom.CONTENT_TYPE_LATEST
