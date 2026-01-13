"""
Test suite for Rainmaker Orchestrator - Aligned with actual API
"""
import pytest
from unittest.mock import patch, AsyncMock
import sys
import os
from fastapi.testclient import TestClient

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'rainmaker_orchestrator'))

from server import app


@pytest.fixture
def client():
    """
    Provide a TestClient for the FastAPI app for use in tests.
    
    Yields:
        TestClient: A configured TestClient instance for making HTTP requests against the application. The client is properly closed when the fixture context exits.
    """
    with TestClient(app) as client:
        yield client


@pytest.fixture
def mock_orchestrator():
    """Mock orchestrator for testing"""
    mock = AsyncMock()
    mock.execute_task = AsyncMock(return_value={"status": "success", "result": "test result"})
    mock.aclose = AsyncMock()
    return mock


class TestHealthEndpoint:
    """Test health check endpoint"""

    @patch('server.app.state.kimi_client.health_check', return_value=True)
    def test_health_returns_200_healthy(self, mock_health_check, client):
        """Test health endpoint returns 200 and healthy"""
        response = client.get('/health')
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'

    @patch('server.app.state.kimi_client.health_check', return_value=False)
    def test_health_returns_200_degraded(self, mock_health_check, client):
        """
        Test that the health endpoint responds with status 200 and a 'degraded' status when the health check indicates degraded service.
        """
        response = client.get('/health')
        assert response.status_code == 200
        assert response.json()['status'] == 'degraded'


class TestExecuteEndpoint:
    """Test execute endpoint"""

    def test_execute_missing_body(self, client):
        """Test execute without body returns 422"""
        response = client.post('/execute', data='')
        assert response.status_code == 422

    def test_execute_missing_context(self, client):
        """
        Test that POST /execute with an empty JSON body returns a 422 status code and includes an error detail.
        """
        response = client.post('/execute', json={})
        assert response.status_code == 422
        data = response.json()
        assert 'detail' in data

    def test_execute_empty_context(self, client):
        """Test execute with empty context returns 422"""
        response = client.post('/execute', json={'task': ''})
        assert response.status_code == 422

    def test_execute_invalid_context_type(self, client):
        """Test execute with non-string context returns 422"""
        response = client.post('/execute', json={'task': 123})
        assert response.status_code == 422

    @patch('server.app.state.orchestrator.execute')
    def test_execute_success(self, mock_execute, client):
        """Test successful task execution"""
        mock_execute.return_value = {"status": "success"}
        response = client.post('/execute', json={'task': 'test task'})
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'

    @patch('server.app.state.orchestrator.execute')
    def test_execute_failed(self, mock_execute, client):
        """Test failed task execution"""
        mock_execute.side_effect = Exception("It failed")
        response = client.post('/execute', json={'task': 'test task'})
        assert response.status_code == 500
        data = response.json()
        assert 'Execution failed' in data['detail']


class TestWorkspaceEndpoints:
    """Test workspace endpoints"""

    @patch('server.Path.is_file')
    @patch('server.Path.exists')
    @patch('server.FileResponse')
    def test_get_workspace_file_success(self, mock_file_response, mock_exists, mock_is_file, client):
        """Test getting a file successfully"""
        mock_exists.return_value = True
        mock_is_file.return_value = True
        response = client.get('/workspace/download/test.txt')
        assert response.status_code == 200

    @patch('server.Path.exists')
    def test_get_workspace_file_not_found(self, mock_exists, client):
        """Test getting a file that does not exist"""
        mock_exists.return_value = False
        response = client.get('/workspace/download/test.txt')
        assert response.status_code == 404

class TestRootEndpoint:
    """Test root endpoint"""

    def test_root_returns_200(self, client):
        """Test root endpoint returns 200 and correct info"""
        response = client.get('/')
        assert response.status_code == 200
        data = response.json()
        assert data['service'] == 'Rainmaker Orchestrator'
        assert data['version'] == '1.0.0'
        assert data['status'] == 'running'

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])