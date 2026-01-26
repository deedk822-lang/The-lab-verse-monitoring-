
import time
import pytest
from unittest.mock import patch
from vaal_ai_empire.services.content_generator import ContentFactory

# Mock provider classes to simulate API calls with delays
class MockSuccessfulProvider:
    def __init__(self, name="success", delay=0.1):
        self.name = name
        self.delay = delay

    def generate(self, prompt, max_tokens):
        time.sleep(self.delay)
        return {"text": f"successful generation from {self.name}", "cost_usd": 0.01, "usage": {"completion_tokens": 10}}

    def generate_content(self, prompt, max_tokens):
        time.sleep(self.delay)
        return {"text": f"successful generation from {self.name}", "provider": self.name, "usage": {"cost_usd": 0.01, "output_tokens": 10}}

    def query_local(self, prompt):
        time.sleep(self.delay)
        return {"text": f"successful generation from {self.name}"}

class MockFailingProvider:
    def __init__(self, name="failure", delay=0.1):
        self.name = name
        self.delay = delay

    def generate(self, prompt, max_tokens):
        time.sleep(self.delay)
        raise ValueError(f"{self.name} provider failed")

    def generate_content(self, prompt, max_tokens):
        time.sleep(self.delay)
        raise ValueError(f"{self.name} provider failed")

    def query_local(self, prompt):
        time.sleep(self.delay)
        raise ValueError(f"{self.name} provider failed")

@pytest.fixture
def mock_providers_fast_success():
    """Fixture where the first provider (groq) succeeds immediately."""
    return {
        "groq": MockSuccessfulProvider(name="groq", delay=0.1),
        "cohere": MockFailingProvider(name="cohere", delay=0.1),
        "mistral": None, "kimi": None, "huggingface": None
    }

@pytest.fixture
def mock_providers_fallback_success():
    """Fixture where groq fails and cohere succeeds."""
    return {
        "groq": MockFailingProvider(name="groq", delay=0.1),
        "cohere": MockSuccessfulProvider(name="cohere", delay=0.1),
        "mistral": None, "kimi": None, "huggingface": None
    }

def _generate_with_fallback_sequential(factory: ContentFactory, prompt: str, max_tokens: int = 500):
    """Stand-alone version of the original sequential fallback logic for testing."""
    priority = ["groq", "cohere", "mistral", "kimi", "huggingface"]
    for provider_name in priority:
        if factory.providers.get(provider_name):
            try:
                # We need to call the internal helper, not the public-facing one
                return factory._call_provider(provider_name, prompt, max_tokens)
            except Exception:
                continue
    raise Exception("All providers failed sequentially")


@patch('vaal_ai_empire.services.content_generator._get_cached_providers')
def test_original_fallback_performance(mock_get_providers, benchmark, mock_providers_fallback_success):
    """Benchmark the original sequential fallback logic."""
    mock_get_providers.return_value = (mock_providers_fallback_success, None, None)

    factory = ContentFactory()

    # Manually re-assign providers after init to ensure mocks are used
    factory.providers = mock_providers_fallback_success

    def run_fallback():
        _generate_with_fallback_sequential(factory, "test prompt")

    benchmark(run_fallback)

@patch('vaal_ai_empire.services.content_generator._get_cached_providers')
def test_new_fallback_performance(mock_get_providers, benchmark, mock_providers_fallback_success):
    """Benchmark the new concurrent fallback logic."""
    mock_get_providers.return_value = (mock_providers_fallback_success, None, None)

    factory = ContentFactory()
    factory.providers = mock_providers_fallback_success

    def run_concurrent_fallback():
        factory._generate_with_concurrent_fallback("test prompt")

    benchmark(run_concurrent_fallback)

@patch('vaal_ai_empire.services.content_generator._get_cached_providers')
def test_correctness_fast_success(mock_get_providers, mock_providers_fast_success):
    """Test that the correct provider is chosen when the first succeeds."""
    mock_get_providers.return_value = (mock_providers_fast_success, None, None)
    factory = ContentFactory()
    factory.providers = mock_providers_fast_success

    result = factory._generate_with_fallback("test prompt")
    assert result['provider'] == 'groq'

@patch('vaal_ai_empire.services.content_generator._get_cached_providers')
def test_correctness_fallback_success(mock_get_providers, mock_providers_fallback_success):
    """Test that the correct provider is chosen when the first fails."""
    mock_get_providers.return_value = (mock_providers_fallback_success, None, None)
    factory = ContentFactory()
    factory.providers = mock_providers_fallback_success

    result = factory._generate_with_fallback("test prompt")
    assert result['provider'] == 'cohere'
