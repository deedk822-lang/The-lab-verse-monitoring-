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
    Create a temporary workspace directory for a test and yield its Path.
    
    Yields:
        Path: Path to the temporary workspace directory. The directory is removed after the test completes.
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
    Provide a mapping of environment variable names to example values for tests.
    
    Returns:
        dict: Mapping of environment variable names to mock string values used by tests.
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
    Return a representative Prometheus-style alert payload used in tests.
    
    Provides a dictionary with keys: `description`, `service`, `severity`, `labels` (containing `env` and `region`), and `annotations` (containing `summary` and `runbook_url`).
    
    Returns:
        dict: Sample alert payload suitable for testing alert handling.
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
    Provides a sample HTTP job payload used by worker tests.
    
    Returns:
        dict: HTTP job configuration with keys 'url', 'method', 'headers', and 'timeout'.
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