import os
import subprocess
from typing import Any, Dict

class FileSystemAgent:
    """
    Agent for handling file system operations in the workspace.
    """
    def __init__(self, workspace_path: str = "./workspace"):
        self.workspace_path = os.path.abspath(workspace_path)
        os.makedirs(self.workspace_path, exist_ok=True)

    def write_file(self, filename: str, content: str) -> None:
        """Writes content to a file in the workspace."""
        file_path = os.path.join(self.workspace_path, filename)
        # Security: ensure file_path is within workspace_path
        if not os.path.abspath(file_path).startswith(self.workspace_path):
            raise ValueError(f"Attempted to write outside workspace: {filename}")

        with open(file_path, "w") as f:
            f.write(content)

    def execute_script(self, filename: str) -> Dict[str, Any]:
        """Executes a Python script in the workspace."""
        file_path = os.path.join(self.workspace_path, filename)
        if not os.path.abspath(file_path).startswith(self.workspace_path):
            return {"status": "error", "stderr": "Access denied"}

        try:
            result = subprocess.run(
                ["python3", file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            return {
                "status": "success" if result.returncode == 0 else "failed",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"status": "failed", "stderr": "Execution timed out"}
        except Exception as e:
            return {"status": "error", "stderr": str(e)}
