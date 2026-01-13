import pytest
import opik
from opik.evaluation import evaluate

from src.rainmaker_orchestrator.agents.healer import SelfHealingAgent

# A mock Kimi client for testing purposes
class MockKimiApiClient:
    async def generate_chat_completion(self, messages: list) -> str:
        # Simulate a plausible hotfix response
        return '{"hotfix": "Restart the pod.", "confidence": 0.85, "impact": "low"}'

@pytest.fixture
def healer():
    # Inject the mock client into the healer
    return SelfHealingAgent(kimi_client=MockKimiApiClient())

@pytest.mark.asyncio
async def test_hotfix_generation_quality(healer):
    """Test hotfix generation meets quality thresholds."""

    test_alerts = [
        {
            "labels": {"service": "api", "severity": "critical"},
            "annotations": {"error_log": "Connection timeout to database"}
        }
    ]

    # Run evaluation
    results = await evaluate(
        dataset=test_alerts,
        task=lambda alert: healer.generate_hotfix(alert),
        scoring_metrics=[
            opik.metrics.Relevance(),
            opik.metrics.Coherence(),
            opik.metrics.ConfidenceScore(min_threshold=0.7)
        ]
    )

    # Assert quality thresholds are met
    assert results.mean_relevance > 0.8
    assert results.mean_coherence > 0.7
    assert results.mean_confidence > 0.7
