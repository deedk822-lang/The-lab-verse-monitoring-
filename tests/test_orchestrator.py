import pytest
import pytest_asyncio
from typing import Dict, Any
from unittest.mock import AsyncMock, patch, MagicMock

from rainmaker_orchestrator.orchestrator import RainmakerOrchestrator


@pytest_asyncio.fixture
async def orchestrator() -> RainmakerOrchestrator:
    """Fixture to create an orchestrator instance."""
    orch: RainmakerOrchestrator = RainmakerOrchestrator()
    yield orch
    await orch.aclose()


@pytest.mark.asyncio
async def test_orchestrator_initialization(orchestrator: RainmakerOrchestrator) -> None:
    """Test orchestrator initializes without errors."""
    assert orchestrator is not None
    assert orchestrator.client is not None
    assert orchestrator.config is not None


@pytest.mark.asyncio
async def test_judge_call_success(orchestrator: RainmakerOrchestrator) -> None:
    """Test successful judge call with mocked API response."""
    with patch.object(orchestrator.client, "post") as mock_post:
        mock_response: MagicMock = AsyncMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"analysis": "success"}'}}]
        }
        mock_post.return_value = mock_response

        result: Dict[str, Any] = await orchestrator._call_judge(
            "auditor",
            "Test context"
        )

        assert result["choices"][0]["message"]["content"] == '{"analysis": "success"}'


@pytest.mark.asyncio
async def test_execute_task_authority_flow(orchestrator: RainmakerOrchestrator) -> None:
    """Test authority task execution."""
    with patch.object(orchestrator, "run_authority_flow", new_callable=AsyncMock) as mock_flow:
        mock_flow.return_value = {"status": "success"}

        result: Dict[str, Any] = await orchestrator.execute_task({
            "type": "authority_task",
            "context": "Test lead data",
        })

        assert result["status"] == "success"
        mock_flow.assert_called_once()


@pytest.mark.asyncio
async def test_execute_task_unsupported_type(orchestrator: RainmakerOrchestrator) -> None:
    """Test unsupported task type handling."""
    result: Dict[str, Any] = await orchestrator.execute_task({
        "type": "unknown_type",
        "context": "Test",
    })

    assert result["status"] == "error"
    assert "not supported" in result["message"]


@pytest.mark.asyncio
async def test_authority_flow_complete(orchestrator: RainmakerOrchestrator) -> None:
    """Test complete 4-Judge authority flow."""
    with patch.object(orchestrator, "_call_judge", new_callable=AsyncMock) as mock_judge:
        mock_judge.return_value = {
            "choices": [{"message": {"content": '{"result": "ok"}'}}]
        }

        result: Dict[str, Any] = await orchestrator.run_authority_flow({
            "lead_id": 123,
            "action": "analyze",
        })

        assert result["status"] == "success"
        assert "audit" in result
        assert "strategy" in result
        assert "implementation" in result
        assert mock_judge.call_count == 3  # auditor, visionary, operator
