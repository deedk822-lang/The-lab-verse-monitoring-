"""
Comprehensive unit tests for RainmakerOrchestrator core functionality.

Tests cover initialization, task execution in various modes,
error handling, timeouts, and workspace management.
"""
import pytest
import tempfile
import subprocess
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from rainmaker_orchestrator.core.orchestrator import RainmakerOrchestrator

@pytest.fixture
def temp_workspace():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

class TestOrchestratorInitialization:
    """Test suite for orchestrator initialization."""

    def test_init_with_default_workspace(self, temp_workspace):
        """Should create default workspace directory."""
        with patch('rainmaker_orchestrator.core.orchestrator.Path.mkdir') as mock_mkdir:
            orchestrator = RainmakerOrchestrator(workspace_path=str(temp_workspace))
            assert orchestrator.workspace_path == temp_workspace
            assert isinstance(orchestrator.workspace_path, Path)

    def test_init_with_custom_workspace(self, temp_workspace):
        """Should use custom workspace path."""
        orchestrator = RainmakerOrchestrator(workspace_path=str(temp_workspace))

        assert orchestrator.workspace_path == temp_workspace
        assert orchestrator.workspace_path.exists()

    def test_init_creates_workspace_directory(self):
        """Should create workspace directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "test_workspace"
            assert not workspace.exists()

            orchestrator = RainmakerOrchestrator(workspace_path=str(workspace))

            assert workspace.exists()
            assert workspace.is_dir()


class TestOrchestratorExecutePython:
    """Test suite for Python code execution."""

    def test_execute_python_simple_success(self, temp_workspace):
        """Should execute simple Python code successfully."""
        orchestrator = RainmakerOrchestrator(workspace_path=str(temp_workspace))
        code = "print('Hello, World!')"

        result = orchestrator.execute(code, mode='python', timeout=10)

        assert result['status'] == 'success'
        assert 'Hello, World!' in result['output']
        assert 'duration' in result

    def test_execute_python_with_error(self, temp_workspace):
        """Should capture Python execution errors."""
        orchestrator = RainmakerOrchestrator(workspace_path=str(temp_workspace))
        code = "raise ValueError('Test error')"

        result = orchestrator.execute(code, mode='python', timeout=10)

        assert result['status'] == 'failed'
        assert 'error' in result

    def test_execute_python_timeout(self, temp_workspace):
        """Should handle execution timeout."""
        orchestrator = RainmakerOrchestrator(workspace_path=str(temp_workspace))
        code = "import time\ntime.sleep(100)"

        with pytest.raises(TimeoutError):
            orchestrator.execute(code, mode='python', timeout=1)


class TestOrchestratorExecuteShell:
    """Test suite for shell command execution."""

    def test_execute_shell_simple_command(self, temp_workspace):
        """Should execute simple shell command."""
        orchestrator = RainmakerOrchestrator(workspace_path=str(temp_workspace))

        result = orchestrator.execute('echo "Hello Shell"', mode='shell', timeout=10)

        assert result['status'] == 'success'
        assert 'Hello Shell' in result['output']

    def test_execute_shell_command_failure(self, temp_workspace):
        """Should capture shell command failures."""
        orchestrator = RainmakerOrchestrator(workspace_path=str(temp_workspace))

        result = orchestrator.execute('exit 1', mode='shell', timeout=10)

        assert result['status'] == 'failed'


class TestOrchestratorErrorHandling:
    """Test suite for error handling and edge cases."""

    def test_execute_with_empty_task(self, temp_workspace):
        """Should handle empty task string."""
        orchestrator = RainmakerOrchestrator(workspace_path=str(temp_workspace))

        result = orchestrator.execute('', mode='python', timeout=10)

        assert 'status' in result

    def test_execute_with_invalid_mode(self, temp_workspace):
        """Should handle invalid execution mode."""
        orchestrator = RainmakerOrchestrator(workspace_path=str(temp_workspace))

        result = orchestrator.execute('test', mode='invalid_mode', timeout=10)

        assert 'status' in result


class TestOrchestratorWorkspaceManagement:
    """Test suite for workspace management."""

    def test_workspace_isolation(self):
        """Should provide isolated workspaces for different instances."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace1 = Path(tmpdir) / "workspace1"
            workspace2 = Path(tmpdir) / "workspace2"

            orch1 = RainmakerOrchestrator(workspace_path=str(workspace1))
            orch2 = RainmakerOrchestrator(workspace_path=str(workspace2))

            assert orch1.workspace_path != orch2.workspace_path
            assert workspace1.exists()
            assert workspace2.exists()
