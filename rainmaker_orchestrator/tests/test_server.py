import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from rainmaker_orchestrator.server import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    """
    Provide a TestClient configured to run the application's lifespan events and use a temporary workspace.
    
    Parameters:
        tmp_path (pathlib.Path): Temporary directory to set as the application's workspace.
        monkeypatch (pytest.MonkeyPatch): Fixture used to patch the application's settings.
    
    Returns:
        TestClient: A FastAPI TestClient instance for the application, yielded within the fixture context.
    """
    from rainmaker_orchestrator.config import settings
    monkeypatch.setattr(settings, "workspace_path", str(tmp_path))
    with TestClient(app) as c:
        yield c


@pytest.fixture
def mock_healer():
    """
    Provide a mock replacement for the healer agent stored at app.state.healer_agent.
    
    Yields:
        mock: A patched mock object that replaces app.state.healer_agent for the duration of the test.
    """
    with patch('rainmaker_orchestrator.server.app.state.healer_agent') as mock:
        yield mock


@pytest.fixture
def mock_orchestrator():
    """
    Provide a pytest fixture that yields a mock replacing app.state.orchestrator in the server app.
    
    Returns:
        mock (unittest.mock.MagicMock): Mock object used in place of the orchestrator.
    """
    with patch('rainmaker_orchestrator.server.app.state.orchestrator') as mock:
        yield mock


class TestHealthEndpoints:
    """Test health and status endpoints."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        assert "service" in response.json()
        assert response.json()["service"] == "Rainmaker Orchestrator"

    def test_health_check_healthy(self, client, monkeypatch):
        """Test health check when services are healthy."""
        mock_kimi = Mock()
        mock_kimi.health_check.return_value = True
        monkeypatch.setattr(app.state, "kimi_client", mock_kimi)

        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["services"]["kimi"] == "up"


class TestAlertEndpoints:
    """Test alert handling endpoints."""

    def test_handle_alert_success(self, client, mock_healer):
        """Test successful alert handling."""
        mock_healer.handle_alert.return_value = {
            "status": "hotfix_generated",
            "blueprint": "def fix():\n    pass",
            "service": "api-service"
        }

        alert_data = {
            "service": "api-service",
            "description": "Error occurred",
            "severity": "critical"
        }

        response = client.post("/webhook/alert", json=alert_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "hotfix_generated"
        assert "blueprint" in data

    def test_handle_alert_failure(self, client, mock_healer):
        """Test alert handling failure."""
        mock_healer.handle_alert.side_effect = Exception("Processing failed")

        alert_data = {
            "service": "api-service",
            "description": "Error occurred"
        }

        response = client.post("/webhook/alert", json=alert_data)
        assert response.status_code == 500

    def test_batch_alerts(self, client, mock_healer):
        """Test batch alert processing."""
        mock_healer.handle_alert.return_value = {
            "status": "hotfix_generated",
            "service": "test"
        }

        alerts = [
            {"service": "service1", "description": "Error 1"},
            {"service": "service2", "description": "Error 2"}
        ]

        response = client.post("/alerts/batch", json=alerts)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["results"]) == 2


class TestExecutionEndpoints:
    """Test task execution endpoints."""

    def test_execute_task_success(self, client, mock_orchestrator):
        """Test successful task execution."""
        mock_orchestrator.execute.return_value = {
            "status": "success",
            "output": "Task completed"
        }

        task_data = {
            "task": "print('hello')",
            "mode": "python"
        }

        response = client.post("/execute", json=task_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_execute_task_timeout(self, client, mock_orchestrator):
        """Test task execution timeout."""
        mock_orchestrator.execute.side_effect = TimeoutError("Timeout")

        task_data = {
            "task": "sleep 1000",
            "mode": "shell"
        }

        response = client.post("/execute", json=task_data)
        assert response.status_code == 408

    def test_execute_async(self, client):
        """Test async task execution."""
        task_data = {
            "task": "echo 'async task'",
            "mode": "shell"
        }

        response = client.post("/execute/async", json=task_data)
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert data["status"] == "queued"


class TestWorkspaceEndpoints:
    """Test workspace management endpoints."""

    def test_list_workspace_files(self, client, tmp_path, monkeypatch):
        """Test listing workspace files."""
        # Create temporary workspace
        (tmp_path / "test.txt").write_text("test content")

        from rainmaker_orchestrator import config
        monkeypatch.setattr(config.settings, "workspace_path", str(tmp_path))

        response = client.get("/workspace/files")
        assert response.status_code == 200
        data = response.json()
        assert "files" in data
        assert "count" in data

    def test_upload_file(self, client, tmp_path, monkeypatch):
        """Test file upload."""
        from rainmaker_orchestrator import config
        monkeypatch.setattr(config.settings, "workspace_path", str(tmp_path))

        files = {"file": ("test.txt", b"test content")}
        response = client.post("/workspace/upload", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "test.txt"
        assert data["status"] == "uploaded"

    def test_create_directory(self, client, tmp_path, monkeypatch):
        """
        Ensure POST /workspace/create-directory creates a directory in the configured workspace.
        
        Patches the application's workspace path to a temporary directory, issues a POST to create "test_dir",
        and asserts the endpoint responds with HTTP 200 and a JSON payload where "status" is "created".
        """
        from rainmaker_orchestrator import config
        monkeypatch.setattr(config.settings, "workspace_path", str(tmp_path))

        response = client.post("/workspace/create-directory?path=test_dir")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "created"


class TestErrorHandling:
    """Test error handling."""

    def test_404_handler(self, client):
        """Test custom 404 handler."""
        response = client.get("/nonexistent")
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert data["error"] == "Not Found"