"""
Shared pytest configuration and fixtures for rainmaker_orchestrator tests.
"""
import pytest
import tempfile
import shutil
from pathlib import Path


@pytest.fixture
def temp_workspace():
    """
    Provide a temporary workspace directory for tests.

    Yields:
        Path: Path to temporary workspace directory

    Cleanup:
        Removes the temporary directory after test completion
    """
    temp_dir = tempfile.mkdtemp(prefix='test_workspace_')
    workspace_path = Path(temp_dir)

    yield workspace_path

    # Cleanup
    if workspace_path.exists():
        shutil.rmtree(workspace_path, ignore_errors=True)


@pytest.fixture
def mock_env_vars():
    """
    Provide a dictionary of mock environment variables.

    Returns:
        dict: Mock environment variables for testing
    """
    return {
        'LOG_LEVEL': 'DEBUG',
        'WORKSPACE_PATH': '/test/workspace',
        'ENVIRONMENT': 'test',
        'KIMI_API_KEY': 'test-key-12345',
        'KIMI_API_BASE': 'http://test-kimi:8000/v1',
        'OLLAMA_API_BASE': 'http://test-ollama:11434/api'
    }


@pytest.fixture
def sample_alert_payload():
    """
    Provide a sample alert payload for testing.

    Returns:
        dict: Sample Prometheus-style alert payload
    """
    return {
        'description': 'Error: Connection timeout to database',
        'service': 'api-service',
        'severity': 'high',
        'labels': {
            'env': 'production',
            'region': 'us-east-1'
        },
        'annotations': {
            'summary': 'Database connection issue',
            'runbook_url': 'https://wiki.example.com/runbooks/db-timeout'
        }
    }


@pytest.fixture
def sample_http_job():
    """
    Provide a sample HTTP job payload for worker testing.

    Returns:
        dict: Sample HTTP job configuration
    """
    return {
        'url': 'http://api.example.com/endpoint',
        'method': 'GET',
        'headers': {
            'User-Agent': 'Test-Worker/1.0',
            'Accept': 'application/json'
        },
        'timeout': 30
    }