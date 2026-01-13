"""Core orchestrator module for task execution and deployment.

Handles task execution, code deployment, and integration with various
execution backends.
"""

import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
import asyncio
import shlex

logger = logging.getLogger(__name__)


class RainmakerOrchestrator:
    """
    Core orchestrator for managing task execution and deployments.

    Provides methods for executing code, deploying services, and managing
    the execution environment.
    """

    def __init__(self, workspace_path: Optional[str] = None):
        """
        Create a RainmakerOrchestrator configured to use a workspace directory.
        
        Parameters:
            workspace_path (Optional[str]): Path for the orchestrator's workspace. If omitted, defaults to "/workspace". The constructor ensures the workspace directory exists (creates it if necessary).
        """
        self.workspace_path = Path(workspace_path or "/workspace")
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"RainmakerOrchestrator initialized with workspace: {self.workspace_path}")

    def execute(
        self,
        task: str,
        mode: str = "general",
        timeout: int = 300,
        environment: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Execute the provided task using the specified mode and return a structured result.
        
        Parameters:
            task (str): Task description or code to execute.
            mode (str): Execution mode; one of "general", "python", "shell", or "docker".
            timeout (int): Maximum allowed execution time in seconds.
            environment (Optional[Dict[str, str]]): Optional environment variables to supply to the execution process.
        
        Returns:
            Dict[str, Any]: Result dictionary with keys:
                - "status": "success" or "failed".
                - "output": Captured standard output (empty on failure or when not applicable).
                - "error": Error message or stderr when failed (may be absent on success).
                - "duration": Execution duration in seconds (when available).
        
        Raises:
            TimeoutError: If execution exceeds the provided timeout.
        """
        logger.info(f"Executing task in {mode} mode (timeout: {timeout}s)")

        try:
            if mode == "python":
                return self._execute_python(task, timeout, environment)
            elif mode == "shell":
                return self._execute_shell(task, timeout, environment)
            elif mode == "docker":
                return self._execute_docker(task, timeout, environment)
            else:
                return self._execute_general(task, timeout, environment)

        except TimeoutError:
            logger.error(f"Task execution timeout after {timeout}s")
            raise
        except Exception as e:
            logger.exception("Task execution failed")
            return {
                "status": "failed",
                "error": f"{e!r}",
                "output": ""
            }

    def _execute_python(
        self,
        code: str,
        timeout: int,
        environment: Optional[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Execute Python source code by writing it to a temporary file, running it with the system Python interpreter, and returning a structured result describing output, duration, and any errors.
        
        Parameters:
            code (str): Python source code to execute.
            timeout (int): Maximum allowed execution time in seconds; a TimeoutError is raised if exceeded.
            environment (Optional[Dict[str, str]]): Optional environment variables to merge with the current process environment for the subprocess.
        
        Returns:
            Dict[str, Any]: Execution result containing at least:
                - "status": "success" if the process exited with code 0, "failed" otherwise.
                - "output": Captured standard output as a string.
                - "duration": Execution time in seconds (float) when available.
                - "error": Captured standard error as a string or an exception representation when applicable.
        
        Raises:
            TimeoutError: If the subprocess exceeds the given timeout.
        """
        import time
        start_time = time.time()

        try:
            # Create temporary file for code
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.py',
                dir=self.workspace_path,
                delete=False
            ) as f:
                f.write(code)
                temp_file = Path(f.name)

            try:
                # Execute using subprocess
                env = environment.copy() if environment else {}
                result = subprocess.run(
                    ["python3", str(temp_file)],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    env={**subprocess.os.environ, **env}
                )

                duration = time.time() - start_time

                if result.returncode == 0:
                    logger.info(f"Python execution successful ({duration:.2f}s)")
                    return {
                        "status": "success",
                        "output": result.stdout,
                        "duration": duration
                    }
                else:
                    logger.error(f"Python execution failed with code {result.returncode}")
                    return {
                        "status": "failed",
                        "output": result.stdout,
                        "error": result.stderr,
                        "duration": duration
                    }
            finally:
                # Cleanup temp file
                temp_file.unlink(missing_ok=True)

        except subprocess.TimeoutExpired:
            logger.error(f"Python execution timeout after {timeout}s")
            raise TimeoutError(f"Execution timeout after {timeout} seconds")
        except Exception as e:
            logger.exception("Python execution error")
            return {
                "status": "failed",
                "error": f"{e!r}",
                "output": ""
            }

    def _execute_shell(
        self,
        command: str,
        timeout: int,
        environment: Optional[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Execute a shell command in the orchestrator workspace and return a structured result.
        
        Parameters:
        	command (str): Shell command to execute; the command will be tokenized and run via subprocess in the orchestrator's workspace directory.
        	timeout (int): Maximum execution time in seconds before raising `TimeoutError`.
        	environment (Optional[Dict[str, str]]): Extra environment variables to merge with the current process environment for the subprocess.
        
        Returns:
        	result (Dict[str, Any]): Dictionary with execution details:
        		- `"status"`: `"success"` if the command exited with code 0, `"failed"` otherwise.
        		- `"output"`: Captured standard output as a string.
        		- `"error"`: Captured standard error as a string (present when `"status"` is `"failed"`).
        		- `"duration"`: Execution time in seconds (float).
        
        Raises:
        	TimeoutError: If the subprocess exceeds the specified timeout.
        """
        import time
        start_time = time.time()

        try:
            env = environment.copy() if environment else {}
            result = subprocess.run(
                shlex.split(command),
                capture_output=True,
                text=True,
                timeout=timeout,
                env={**subprocess.os.environ, **env},
                cwd=self.workspace_path
            )

            duration = time.time() - start_time

            if result.returncode == 0:
                logger.info(f"Shell execution successful ({duration:.2f}s)")
                return {
                    "status": "success",
                    "output": result.stdout,
                    "duration": duration
                }
            else:
                logger.error(f"Shell execution failed with code {result.returncode}")
                return {
                    "status": "failed",
                    "output": result.stdout,
                    "error": result.stderr,
                    "duration": duration
                }

        except subprocess.TimeoutExpired:
            logger.error(f"Shell execution timeout after {timeout}s")
            raise TimeoutError(f"Execution timeout after {timeout} seconds")
        except Exception as e:
            logger.exception("Shell execution error")
            return {
                "status": "failed",
                "error": f"{e!r}",
                "output": ""
            }

    def _execute_docker(
        self,
        task: str,
        timeout: int,
        environment: Optional[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Return a not-implemented result for Docker-based execution.
        
        Returns:
            result (Dict[str, Any]): A dictionary with:
                - "status": "failed"
                - "error": explanation string
                - "output": empty string
                - "message": guidance to use 'python' or 'shell' mode
        """
        logger.warning("Docker execution not yet implemented")
        return {
            "status": "failed",
            "error": "Docker execution not yet implemented",
            "output": "",
            "message": "Use 'python' or 'shell' mode for now"
        }

    def _execute_general(
        self,
        task: str,
        timeout: int,
        environment: Optional[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Determine the appropriate executor for a generic task string and run it.
        
        Parameters:
            task (str): Task content or command to execute; may be Python code or a shell command.
            timeout (int): Maximum allowed execution time in seconds.
            environment (Optional[Dict[str, str]]): Environment variables to apply to the execution.
        
        Returns:
            Dict[str, Any]: Execution result dictionary containing keys such as `status`, `output`, `error` and `duration` depending on the outcome.
        """
        # Try to detect the task type
        if task.strip().startswith(('def ', 'import ', 'from ', 'class ')):
            return self._execute_python(task, timeout, environment)
        elif task.strip().startswith(('#!/bin/', 'cd ', 'ls ', 'echo ')):
            return self._execute_shell(task, timeout, environment)
        else:
            # Default to shell execution
            return self._execute_shell(task, timeout, environment)

    def deploy(
        self,
        service: str,
        code: str,
        deployment_type: str = "hotfix"
    ) -> Dict[str, Any]:
        """
        Deploy the given code to a named service by saving it under the orchestrator's workspace and returning deployment metadata.
        
        Parameters:
            service (str): Target service name used to group deployment files.
            code (str): Source code or patch content to persist for the deployment.
            deployment_type (str): Deployment category, e.g. "hotfix", "update", or "rollback".
        
        Returns:
            dict: Deployment result with keys:
                - status (str): "deployed" on success, "failed" on error.
                - id (str): Short (8-character) deployment identifier.
                - service (str): The service name provided.
                - type (str): The deployment_type provided.
                - path (str): Filesystem path to the saved deployment file (present on success).
                - error (str): Error representation (present on failure).
        """
        import uuid
        deployment_id = str(uuid.uuid4())[:8]

        logger.info(f"Deploying {deployment_type} to service '{service}' (ID: {deployment_id})")

        try:
            # Save the code to workspace
            deployment_path = self.workspace_path / "deployments" / service
            deployment_path.mkdir(parents=True, exist_ok=True)

            code_file = deployment_path / f"{deployment_type}_{deployment_id}.py"
            code_file.write_text(code)

            logger.info(f"Code saved to {code_file}")

            # In a real implementation, this would:
            # 1. Run tests on the code
            # 2. Create a deployment package
            # 3. Push to the target service
            # 4. Monitor the deployment
            # 5. Rollback on failure

            # For now, we simulate successful deployment
            logger.info(f"Deployment {deployment_id} completed successfully")

            return {
                "status": "deployed",
                "id": deployment_id,
                "service": service,
                "type": deployment_type,
                "path": str(code_file)
            }

        except Exception as e:
            logger.exception(f"Deployment failed for service '{service}'")
            return {
                "status": "failed",
                "id": deployment_id,
                "service": service,
                "type": deployment_type,
                "error": f"{e!r}"
            }

    def rollback(
        self,
        service: str,
        deployment_id: str
    ) -> Dict[str, Any]:
        """
        Rolls back a deployment for the given service.
        
        Returns:
            dict: On success: `{"status": "rolled_back", "service": service, "deployment_id": deployment_id}`.
                  On failure: `{"status": "failed", "service": service, "deployment_id": deployment_id, "error": <repr of exception>)}`.
        """
        logger.info(f"Rolling back deployment {deployment_id} for service '{service}'")

        try:
            # In a real implementation, this would:
            # 1. Identify the previous stable version
            # 2. Redeploy that version
            # 3. Verify the rollback

            return {
                "status": "rolled_back",
                "service": service,
                "deployment_id": deployment_id
            }

        except Exception as e:
            logger.exception(f"Rollback failed for service '{service}'")
            return {
                "status": "failed",
                "service": service,
                "deployment_id": deployment_id,
                "error": f"{e!r}"
            }

    def get_deployment_status(
        self,
        service: str,
        deployment_id: str
    ) -> Dict[str, Any]:
        """
        Retrieve the current status of a deployment for a service.
        
        Returns:
            dict: Deployment metadata with keys:
                - `deployment_id` (str): The requested deployment identifier.
                - `service` (str): The service name.
                - `status` (str): Current deployment status (stubbed as `"unknown"`).
                - `message` (str): Human-readable note about status tracking.
        """
        logger.info(f"Checking deployment status for {deployment_id}")

        # In a real implementation, this would query the deployment system
        return {
            "deployment_id": deployment_id,
            "service": service,
            "status": "unknown",
            "message": "Status tracking not yet implemented"
        }