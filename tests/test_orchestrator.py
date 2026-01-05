"""
Test suite for Rainmaker Orchestrator - Aligned with actual API
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'rainmaker_orchestrator'))

from server import app, validate_execute_request, cleanup_orchestrator


@pytest.fixture
def client():
    """Create Flask test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
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

    @patch('server.orchestrator.config.validate')
    @patch('os.path.exists', return_value=True)
    @patch('os.access', return_value=True)
    def test_health_returns_200_healthy(self, mock_access, mock_exists, mock_validate, client):
        """Test health endpoint returns 200 and healthy"""
        mock_validate.return_value = []
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert data['service'] == 'rainmaker-orchestrator'

    @patch('server.orchestrator.config.validate')
    def test_health_returns_200_degraded(self, mock_validate, client):
        """Test health endpoint returns 200 and degraded if config missing"""
        mock_validate.return_value = ['KIMI_API_KEY']
        response = client.get('/health')
        assert response.status_code == 200
        assert response.get_json()['status'] == 'degraded'


class TestExecuteEndpoint:
    """Test execute endpoint"""

    def test_execute_missing_body(self, client):
        """Test execute without body returns 400"""
        response = client.post('/execute',
                               content_type='application/json',
                               data='')
        assert response.status_code == 400

    def test_execute_missing_context(self, client):
        """Test execute without context field returns 400"""
        response = client.post('/execute', json={})
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'context' in data['error'].lower()

    def test_execute_empty_context(self, client):
        """Test execute with empty context returns 400"""
        response = client.post('/execute', json={'context': ''})
        assert response.status_code == 400

    def test_execute_invalid_context_type(self, client):
        """Test execute with non-string context returns 400"""
        response = client.post('/execute', json={'context': 123})
        assert response.status_code == 400

    def test_execute_invalid_filename(self, client):
        """Test execute with path traversal in filename returns 400"""
        response = client.post('/execute', json={'context': 'test', 'output_filename': '../etc/passwd'})
        assert response.status_code == 400

    @patch('server.orchestrator')
    def test_execute_success(self, mock_orch, client):
        """Test successful task execution"""
        mock_orch.execute_task = AsyncMock(return_value={"status": "success"})
        response = client.post('/execute', json={'context': 'test task'})
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'

    @patch('server.orchestrator')
    def test_execute_failed(self, mock_orch, client):
        """Test failed task execution"""
        mock_orch.execute_task = AsyncMock(return_value={"status": "failed", "message": "It failed"})
        response = client.post('/execute', json={'context': 'test task'})
        assert response.status_code == 422
        data = response.get_json()
        assert data['status'] == 'failed'
        assert 'It failed' in data['error']

    def test_execute_with_request_id_header(self, client):
        """Test execute respects X-Request-ID header"""
        with patch('server.orchestrator.execute_task', new=AsyncMock(return_value={"status": "success"})):
            response = client.post('/execute',
                                   headers={'X-Request-ID': 'test-123'},
                                   json={'context': 'test'})
            assert response.status_code == 200
            data = response.get_json()
            assert data['request_id'] == 'test-123'


class TestValidation:
    """Test validation functions"""

    def test_validate_execute_request_valid(self):
        """Test validation with valid request"""
        data = {'context': 'test task'}
        is_valid, error = validate_execute_request(data)
        assert is_valid is True
        assert error == ""

    def test_validate_execute_request_missing_context(self):
        """Test validation with missing context"""
        data = {}
        is_valid, error = validate_execute_request(data)
        assert is_valid is False
        assert 'context' in error.lower()

    def test_validate_execute_request_with_filename(self):
        """Test validation with valid filename"""
        data = {'context': 'test', 'output_filename': 'script.py'}
        is_valid, error = validate_execute_request(data)
        assert is_valid is True

    def test_validate_execute_request_invalid_filename(self):
        """Test validation with invalid filename"""
        data = {'context': 'test', 'output_filename': '../script.py'}
        is_valid, error = validate_execute_request(data)
        assert is_valid is False
        assert 'invalid characters' in error.lower()


class TestWorkspaceEndpoints:
    """Test workspace endpoints"""

    @patch('server.orchestrator.fs.read_file')
    def test_get_workspace_file_success(self, mock_read, client):
        """Test getting a file successfully"""
        mock_read.return_value = {"status": "success", "content": "hello"}
        response = client.get('/workspace/files/test.txt')
        assert response.status_code == 200
        data = response.get_json()
        assert data['content'] == 'hello'

    @patch('server.orchestrator.fs.read_file')
    def test_get_workspace_file_not_found(self, mock_read, client):
        """Test getting a file that does not exist"""
        mock_read.return_value = {"status": "error", "message": "File not found"}
        response = client.get('/workspace/files/test.txt')
        assert response.status_code == 404


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
