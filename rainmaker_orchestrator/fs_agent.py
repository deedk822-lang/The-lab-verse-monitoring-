import os
import subprocess
import logging
from typing import Dict, Any

from rainmaker_orchestrator.agents.healer import SelfHealingAgent

logger: logging.Logger = logging.getLogger("fs_agent")


class FileSystemAgent:
    """Handles secure file system operations and script execution."""

    def __init__(self, workspace_path: str = "./workspace"):
        """Initializes the agent and creates the workspace directory if it doesn't exist."""
        self.workspace_path = os.path.abspath(workspace_path)
        os.makedirs(self.workspace_path, exist_ok=True)
        logger.info(f"FileSystemAgent initialized at {self.workspace_path}")

    def _get_safe_path(self, filename: str) -> str:
        """
        Constructs a safe file path within the workspace and prevents directory traversal.
        """
        if ".." in filename or filename.startswith("/"):
            raise ValueError("Invalid filename. Directory traversal is not allowed.")
        return os.path.join(self.workspace_path, filename)

    def write_file(self, filename: str, content: str) -> None:
        """Writes content to a specified file within the workspace."""
        safe_path = self._get_safe_path(filename)
        try:
            with open(safe_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"Successfully wrote to {safe_path}")
        except IOError as e:
            logger.error(f"Error writing to file {safe_path}: {e}")
            raise

    def execute_script(self, filename: str) -> Dict[str, Any]:
        """
        Executes a script from the workspace, using the SelfHealingAgent for security validation.
        """
        script_path = self._get_safe_path(filename)
        if not os.path.exists(script_path):
            logger.error(f"Script not found at path: {script_path}")
            return {"status": "error", "message": f"Script not found: {script_path}"}

        command = f"python {script_path}"

        try:
            # Integrate the SelfHealingAgent to validate and parse the command
            parsed_command = SelfHealingAgent.safe_parse_command(command)
            logger.info(f"Executing validated command: {parsed_command}")

            process = subprocess.run(
                parsed_command,
                capture_output=True,
                text=True,
                check=False,
                timeout=60,
            )

            if process.returncode == 0:
                logger.info(f"Script '{filename}' executed successfully.")
                return {
                    "status": "success",
                    "stdout": process.stdout,
                    "stderr": process.stderr,
                }
            else:
                logger.warning(
                    f"Script '{filename}' failed with exit code {process.returncode}."
                )
                return {
                    "status": "error",
                    "stdout": process.stdout,
                    "stderr": process.stderr,
                    "exit_code": process.returncode,
                }
        except ValueError as ve:
            logger.error(f"Command validation failed for '{command}': {ve}")
            return {"status": "error", "message": str(ve)}
        except subprocess.TimeoutExpired as te:
            logger.error(f"Script execution timed out for '{filename}'.")
            return {
                "status": "error",
                "message": "Script execution timed out.",
                "stdout": te.stdout,
                "stderr": te.stderr,
            }
        except Exception as e:
            logger.error(f"An unexpected error occurred while executing '{filename}': {e}")
            return {"status": "error", "message": str(e)}
