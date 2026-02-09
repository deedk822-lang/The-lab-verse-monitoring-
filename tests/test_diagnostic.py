"""Tests for agent/nodes/diagnostic.py."""

import sys
from unittest.mock import AsyncMock, MagicMock, Mock, patch
import pytest

sys.modules.setdefault("agent.config", MagicMock())
sys.modules.setdefault("agent.tools.hf_model_loader", MagicMock())
sys.modules.setdefault("vaal_ai_empire", MagicMock())
sys.modules.setdefault("vaal_ai_empire.api", MagicMock())
sys.modules.setdefault("vaal_ai_empire.api.sanitizers", MagicMock())


def test_run_diagnostic_success():
    from agent.nodes.diagnostic import run_diagnostic

    state = Mock()
    state.run_id = "run-1"
    state.repo_full_name = "org/repo"
    state.branch = "main"
    state.workflow_name = "CI"
    state.error_message = "failed"
    state.failed_jobs = []
    state.logs = "boom"
    state.root_cause = None
    state.confidence_score = None

    with patch("agent.nodes.diagnostic.model_loader") as loader, patch(
        "agent.nodes.diagnostic.sanitize_prompt", side_effect=lambda v, max_length=0: v
    ):
        loader.load_model = AsyncMock()
        loader.inference = AsyncMock(
            return_value='{"root_cause":"Config error","confidence":0.9,"fix_category":"config","recommended_action":"Fix","monitoring_specific":"None"}'
        )
        loader.unload_model = Mock()

        import asyncio
        result = asyncio.run(run_diagnostic(state))

    assert result.root_cause == "Config error"
    assert result.confidence_score == 0.9


def test_run_diagnostic_invalid_json_raises():
    from agent.nodes.diagnostic import run_diagnostic

    state = Mock()
    state.repo_full_name = "org/repo"
    state.branch = "main"
    state.workflow_name = "CI"
    state.error_message = "failed"
    state.failed_jobs = []
    state.logs = "boom"

    with patch("agent.nodes.diagnostic.model_loader") as loader, patch(
        "agent.nodes.diagnostic.sanitize_prompt", side_effect=lambda v, max_length=0: v
    ):
        loader.load_model = AsyncMock()
        loader.inference = AsyncMock(return_value="not json")

        with pytest.raises(ValueError, match="valid JSON"):
            import asyncio
            asyncio.run(run_diagnostic(state))
