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
    Create and provide a temporary workspace directory for a test.
    
    Yields:
        Path: Path to the temporary workspace directory
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
    Mock environment variables for tests.
    
    Returns:
        dict: Mapping of environment variable names to test values. Keys include
            `LOG_LEVEL`, `WORKSPACE_PATH`, `ENVIRONMENT`, `KIMI_API_KEY`,
            `KIMI_API_BASE`, and `OLLAMA_API_BASE`.
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
    Sample Prometheus-style alert payload for use in tests.
    
    Returns:
        dict: Alert payload with keys:
            - `description` (str): human-readable description of the alert
            - `service` (str): affected service name
            - `severity` (str): alert severity level
            - `labels` (dict): string key/value pairs for alert labels (e.g., `env`, `region`)
            - `annotations` (dict): string key/value pairs for alert annotations (e.g., `summary`, `runbook_url`)
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
    Return a sample HTTP job payload used by worker tests.
    
    Returns:
        dict: HTTP job configuration with keys:
            url (str): Request URL.
            method (str): HTTP method (e.g., 'GET').
            headers (dict): Request headers.
            timeout (int): Timeout in seconds.
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