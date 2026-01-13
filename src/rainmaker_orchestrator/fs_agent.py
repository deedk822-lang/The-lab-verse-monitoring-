import os
import subprocess
import sys
import re
import json
from werkzeug.utils import secure_filename
import resource
 feature/elite-ci-cd-pipeline-1070897568806221897
import shlex
from typing import Set, Dict, Any

import tempfile

# Whitelist of safe commands. Using basename to handle full paths like /usr/bin/python
ALLOWED_COMMANDS: Set[str] = {"python", "pytest", "python3"}

class FileSystemAgent:
    def __init__(self, workspace_path="/workspace", max_file_size=10*1024*1024):  # 10MB max
        if 'pytest' in sys.modules:


import tempfile


class FileSystemAgent:
    def __init__(
        self, workspace_path="/workspace", max_file_size=10 * 1024 * 1024
    ):  # 10MB max
        if "pytest" in sys.modules:
 main
            self.workspace = tempfile.mkdtemp()
        else:
            self.workspace = os.path.realpath(workspace_path)
        self.max_size = max_file_size
        os.makedirs(self.workspace, exist_ok=True)

    def _is_safe_path(self, path: str) -> bool:
        """Prevents path traversal and symlink attacks"""
        safe_name = secure_filename(path)
        full_path = os.path.join(self.workspace, safe_name)
        resolved_path = os.path.realpath(full_path)
        return os.path.commonpath([self.workspace, resolved_path]) == self.workspace

    def write_file(self, filename: str, content: str) -> dict:
        """Secure file write with size limits"""
        safe_name = secure_filename(filename)
        if not self._is_safe_path(safe_name):
            return {"status": "error", "message": "Path traversal detected"}

        if len(content.encode("utf-8")) > self.max_size:
            return {
                "status": "error",
                "message": f"File exceeds {self.max_size / (1024*1024)}MB limit",
            }

        full_path = os.path.join(self.workspace, safe_name)
        try:
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            return {"status": "success", "path": full_path, "filename": safe_name}
        except Exception as e:
            return {"status": "error", "message": f"Disk write failed: {str(e)}"}

    def read_file(self, filename: str) -> dict:
        """Secure file read"""
        safe_name = secure_filename(filename)
        if not self._is_safe_path(safe_name):
            return {"status": "error", "message": "Path traversal detected"}

        full_path = os.path.join(self.workspace, safe_name)
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            return {"status": "success", "content": content}
        except FileNotFoundError:
            return {"status": "error", "message": "File not found"}
        except Exception as e:
            return {"status": "error", "message": f"Disk read failed: {str(e)}"}

 feature/elite-ci-cd-pipeline-1070897568806221897
    def execute_script(self, filename: str, timeout: int = 30, mem_limit_mb: int = 128) -> Dict[str, Any]:
        """
        Executes a python script safely using a whitelist.
        """
        safe_name = secure_filename(filename)
        if not self._is_safe_path(safe_name):
            return {"status": "error", "message": "Security violation: Cannot execute outside workspace."}

        command = f"{sys.executable} {safe_name}"

    def execute_script(
        self, filename: str, timeout: int = 10, mem_limit_mb: int = 128
    ) -> dict:
        """
        Executes a Python script found in the workspace.
        Captures stdout and stderr.
        """
        safe_name = secure_filename(filename)
        if not self._is_safe_path(safe_name):
            return {
                "status": "error",
                "message": "Security violation: Cannot execute outside workspace.",
            }

        full_path = os.path.join(self.workspace, safe_name)
 main

        def set_limits():
            # Limit virtual memory (RLIMIT_AS)
            resource.setrlimit(
                resource.RLIMIT_AS,
 feature/elite-ci-cd-pipeline-1070897568806221897
                (mem_limit_mb * 1024 * 1024, mem_limit_mb * 1024 * 1024)
            )

        try:
            cmd_parts = shlex.split(command)

            if not cmd_parts:
                return {"status": "error", "message": "Empty command"}

            if os.path.basename(cmd_parts[0]) not in ALLOWED_COMMANDS:
                 logger.warning(f"Blocked command attempt: {cmd_parts[0]}")
                 return {
                     "status": "failure",
                     "message": f"Command '{os.path.basename(cmd_parts[0])}' not in whitelist"
                 }

            result = subprocess.run(
                cmd_parts,
                shell=False,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
                cwd=self.workspace,
                env={"PYTHONUNBUFFERED": "1"},
                preexec_fn=set_limits
            )

            status = "success" if result.returncode == 0 else "failure"

            return {
                "status": status,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }

        except subprocess.TimeoutExpired:
            return {"status": "failure", "message": f"Execution timed out after {timeout} seconds."}

                (mem_limit_mb * 1024 * 1024, mem_limit_mb * 1024 * 1024),
            )

        try:
            # Run the script in a subprocess
            result = subprocess.run(
                [sys.executable, full_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.workspace,
                env={"PYTHONUNBUFFERED": "1"},  # Minimal env
                preexec_fn=set_limits,
            )

            if result.returncode == 0:
                return {
                    "status": "success",
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }
            else:
                return {
                    "status": "failure",
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode,
                }

        except subprocess.TimeoutExpired:
            return {
                "status": "failure",
                "message": f"Execution timed out after {timeout} seconds.",
            }
 main
        except Exception as e:
            return {"status": "error", "message": str(e)}
