import os
import subprocess
import sys
import shlex
import resource
from typing import Set, Dict, Any
from werkzeug.utils import secure_filename

# Whitelist of safe commands
ALLOWED_COMMANDS: Set[str] = {"python", "pytest", "python3"}

class FileSystemAgent:
    def __init__(self, workspace_path="./workspace", max_file_size=10*1024*1024):
        self.workspace = os.path.realpath(workspace_path)
        self.max_size = max_file_size
        os.makedirs(self.workspace, exist_ok=True)

    def _is_safe_path(self, path: str) -> bool:
        """Prevents path traversal and symlink attacks"""
        safe_name = secure_filename(path)
        full_path = os.path.join(self.workspace, safe_name)
        resolved_path = os.path.realpath(full_path)
        return os.path.commonpath([self.workspace, resolved_path]) == self.workspace

    def write_file(self, filename: str, content: str) -> Dict[str, Any]:
        """Secure file write with size limits"""
        if not self._is_safe_path(filename):
            return {"status": "error", "message": "Path traversal detected"}

        if len(content.encode("utf-8")) > self.max_size:
            return {"status": "error", "message": "File exceeds size limit"}

        full_path = os.path.join(self.workspace, secure_filename(filename))
        try:
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            return {"status": "success", "path": full_path}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def execute_script(self, filename: str, timeout: int = 30, mem_limit_mb: int = 128) -> Dict[str, Any]:
        """Executes a python script safely using a whitelist."""
        if not self._is_safe_path(filename):
            return {"status": "error", "message": "Security violation"}

        command = f"{sys.executable} {secure_filename(filename)}"

        def set_limits():
            resource.setrlimit(resource.RLIMIT_AS, (mem_limit_mb * 1024 * 1024, mem_limit_mb * 1024 * 1024))

        try:
            cmd_parts = shlex.split(command)
            result = subprocess.run(
                cmd_parts,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.workspace,
                preexec_fn=set_limits
            )
            return {
                "status": "success" if result.returncode == 0 else "failure",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"status": "failure", "message": "Timeout"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
