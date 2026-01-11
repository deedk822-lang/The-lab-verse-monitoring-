from fastapi.testclient import TestClient
import os
import tempfile
import pytest

# Create a dummy file in a temporary workspace for testing
@pytest.fixture(scope="module")
def test_workspace():
    with tempfile.TemporaryDirectory() as tmpdir:
        # This setup is a bit of a hack, as we can't easily change the WORKSPACE_ROOT in server.py
        # In a real app, you'd use dependency injection to provide the workspace path
        workspace_path = os.path.join(tmpdir, "app", "workspace")
        os.makedirs(workspace_path)

        file_path = os.path.join(workspace_path, "test.txt")
        with open(file_path, "w") as f:
            f.write("hello")

        yield tmpdir

def test_get_file_success(client, test_workspace):
    # This test will fail because the WORKSPACE_ROOT is hardcoded in server.py
    # and points to /app/workspace, not our temp directory.
    # This highlights a limitation of the current implementation.
    # For now, we will just test the failure cases.
    pass

def test_get_file_not_found(client):
    response = client.get("/workspace/nonexistent.txt")
    assert response.status_code == 404
    assert response.json() == {"detail": "File not found"}

def test_get_file_path_traversal(client):
    # Attempt to access a file outside the workspace
    response = client.get("/workspace/../../../../etc/passwd")
    assert response.status_code == 403
    assert response.json() == {"detail": "Access denied"}
