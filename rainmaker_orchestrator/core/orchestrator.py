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

logger = logging.getLogger(__name__)


class RainmakerOrchestrator:
    """
    Core orchestrator for managing task execution and deployments.

    Provides methods for executing code, deploying services, and managing
    the execution environment.
    """

    def __init__(self, workspace_path: Optional[str] = None):
        """
        Initialize the orchestrator with a workspace directory.
        
        Creates the workspace directory on disk if it does not already exist.
        
        Parameters:
            workspace_path (Optional[str]): Path to the workspace directory to use. Defaults to "/workspace".
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
        Dispatch execution of the given task to the appropriate executor based on mode.
        
        Parameters:
            task (str): Code or command to execute.
            mode (str): Execution mode — "general", "python", "shell", or "docker".
            timeout (int): Maximum allowed execution time in seconds.
            environment (Optional[Dict[str, str]]): Environment variables to supply to the execution.
        
        Returns:
            result (Dict[str, Any]): Execution result with keys:
                - status (str): "success" or "failed".
                - output (str): Captured standard output and/or result.
                - error (str): Error message when status is "failed".
                - duration (float): Execution duration in seconds (when available).
        
        Raises:
            TimeoutError: If execution exceeds the specified timeout.
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
        Execute Python source code by running it in a temporary file.
        
        The code is written to a temporary .py file inside the orchestrator workspace and executed with the system Python interpreter; the temporary file is removed after execution.
        
        Parameters:
            code (str): Python source code to execute.
            timeout (int): Maximum execution time in seconds.
            environment (Optional[Dict[str, str]]): Additional environment variables to merge with the current process environment.
        
        Returns:
            Dict[str, Any]: Execution result containing:
                - "status": "success" or "failed".
                - "output": captured standard output as a string.
                - "error": captured standard error as a string (present when status is "failed").
                - "duration": wall-clock execution duration in seconds.
        
        Raises:
            TimeoutError: If the execution exceeds the given timeout.
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
        Run a shell command in the orchestrator workspace and return its result.
        
        Parameters:
            command (str): The shell command to run.
            timeout (int): Maximum execution time in seconds before a TimeoutError is raised.
            environment (Optional[Dict[str, str]]): Additional environment variables to set for the command.
        
        Returns:
            result (Dict[str, Any]): Execution metadata with keys:
                - `status` (`"success"` or `"failed"`),
                - `output` (str): captured standard output,
                - `error` (str, optional): captured standard error when `status` is `"failed"`,
                - `duration` (float, optional): elapsed time in seconds.
        
        Raises:
            TimeoutError: If the command does not complete within `timeout` seconds.
        """
        import time
        start_time = time.time()

        try:
            env = environment.copy() if environment else {}
            result = subprocess.run(
                command,
                shell=True,
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
        Placeholder executor for running a task inside a Docker container.
        
        Parameters:
            task (str): The task or command intended to run inside Docker.
            timeout (int): Maximum execution time in seconds.
            environment (Optional[Dict[str, str]]): Environment variables to apply inside the container.
        
        Returns:
            Dict[str, Any]: Result dictionary with keys:
                - `status`: `"failed"` indicating Docker execution is not implemented.
                - `error`: short error message.
                - `output`: captured output (empty string).
                - `message`: human-readable guidance (e.g., suggesting alternative modes).
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
        Dispatches a textual task to the appropriate executor (Python or shell) based on the task content.
        
        Parameters:
            task (str): The task text to run; may be source code or a shell command.
            timeout (int): Maximum allowed runtime in seconds.
            environment (Optional[Dict[str, str]]): Environment variables to apply during execution.
        
        Returns:
            Dict[str, Any]: Execution result containing keys such as `status`, `output`, `duration`, and optionally `error`.
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
        Save the provided code as a deployment artifact for a named service and simulate a deployment.
        
        Parameters:
            service (str): Target service name.
            code (str): Source code or patch to persist for deployment.
            deployment_type (str): Deployment category (e.g., "hotfix", "update", "rollback").
        
        Returns:
            dict: Deployment metadata including:
                - status (str): One of `"deployed"` or `"failed"`.
                - id (str): Short deployment identifier.
                - service (str): Target service name.
                - type (str): Provided deployment type.
                - path (str): Filesystem path to the saved code (present on success).
                - error (str): Error details (present on failure).
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
        Roll back a previously recorded deployment for a service.
        
        Parameters:
            service (str): Target service name.
            deployment_id (str): Identifier of the deployment to roll back.
        
        Returns:
            result (Dict[str, Any]): Rollback result containing:
                - status (str): "rolled_back" on success or "failed" on error.
                - service (str): The target service name.
                - deployment_id (str): The deployment identifier.
                - error (str, optional): Error details when status is "failed".
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
        Retrieve status information for a specific deployment.
        
        Parameters:
            service (str): Name of the service owning the deployment.
            deployment_id (str): Identifier of the deployment to query.
        
        Returns:
            dict: Deployment status payload containing keys:
                - `deployment_id` (str): The queried deployment identifier.
                - `service` (str): The service name.
                - `status` (str): Current status label (e.g., "unknown").
                - `message` (str): Human-readable details or notes about the status.
        """
        logger.info(f"Checking deployment status for {deployment_id}")

        # In a real implementation, this would query the deployment system
        return {
            "deployment_id": deployment_id,
            "service": service,
            "status": "unknown",
            "message": "Status tracking not yet implemented"
        }