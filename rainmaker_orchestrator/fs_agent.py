import subprocess
from typing import Any, Dict


class FileSystemAgent:
    """Agent for interacting with the file system and executing scripts."""

    def __init__(self, workspace_path: str):
        self.workspace_path = workspace_path

    def write_file(self, filename: str, content: str) -> None:
        """Write content to a file."""
        with open(filename, 'w') as f:
            f.write(content)

    def execute_script(self, filename: str) -> Dict[str, Any]:
        """Execute a Python script and return the result."""
        try:
            result = subprocess.run(['python3', filename], capture_output=True, text=True)
            if result.returncode == 0:
                return {"status": "success", "stdout": result.stdout}
            else:
                return {"status": "error", "stderr": result.stderr}
        except Exception as e:
            return {"status": "error", "stderr": str(e)}
