"""FileSystem Agent for Rainmaker Orchestrator."""
import logging
import subprocess
from typing import Any, Dict

logger = logging.getLogger("fs_agent")

class FileSystemAgent:
    """Agent for interacting with the file system."""
    def __init__(self, workspace_path: str = "./workspace") -> None:
        self.workspace_path = workspace_path

    def write_file(self, filename: str, content: str) -> None:
        """Write content to a file."""
        import os
        path = os.path.join(self.workspace_path, filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
        logger.info(f"Wrote to {path}")

    def execute_script(self, filename: str) -> Dict[str, Any]:
        """Execute a script and return results."""
        import os
        path = os.path.join(self.workspace_path, filename)
        try:
            result = subprocess.run(["python3", path], capture_output=True, text=True, check=False)
            if result.returncode == 0:
                return {"status": "success", "stdout": result.stdout}
            else:
                return {"status": "error", "stderr": result.stderr}
        except Exception as e:
            return {"status": "error", "stderr": str(e)}
