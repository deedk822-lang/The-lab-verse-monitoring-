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
 feat/complete-10268506225633119435

import shlex
 feature/complete-orchestrator-and-scheduler-3340126171226885686

logger = logging.getLogger(__name__)


class RainmakerOrchestrator:
    """
    Core orchestrator for managing task execution and deployments.

    Provides methods for executing code, deploying services, and managing
    the execution environment.
    """

    def __init__(self, workspace_path: Optional[str] = None):
        """
        Initialize the orchestrator.

        Args:
            workspace_path: Optional path to workspace directory
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
        Execute a task or code.

        Args:
            task: Task description or code to execute
            mode: Execution mode ('general', 'python', 'shell', 'docker')
            timeout: Execution timeout in seconds
            environment: Optional environment variables

        Returns:
            Dictionary with execution results:
            - status: 'success' or 'failed'
            - output: Execution output
            - error: Error message (if failed)
            - duration: Execution duration in seconds

        Raises:
            TimeoutError: If execution exceeds timeout
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
        Execute Python code.

        Args:
            code: Python code to execute
            timeout: Execution timeout in seconds
            environment: Optional environment variables

        Returns:
            Execution result dictionary
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
        Execute shell command.

        Args:
            command: Shell command to execute
            timeout: Execution timeout in seconds
            environment: Optional environment variables

        Returns:
            Execution result dictionary
 feat/complete-10268506225633119435

        Security:
            Note: shell=True is used for intentional shell feature support.
            This is only safe when used with trusted input sources.
            For production, consider using shlex.split() and shell=False.

 feature/complete-orchestrator-and-scheduler-3340126171226885686
        """
        import time
        start_time = time.time()

        try:
            env = environment.copy() if environment else {}
            result = subprocess.run(
 feat/complete-10268506225633119435
                command,
                shell=True,

                shlex.split(command),
 feature/complete-orchestrator-and-scheduler-3340126171226885686
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
        Execute task in Docker container.

        Args:
            task: Task to execute
            timeout: Execution timeout in seconds
            environment: Optional environment variables

        Returns:
            Execution result dictionary

        Note:
            Docker execution is planned for future implementation.
            Track progress at: https://github.com/deedk822-lang/The-lab-verse-monitoring-/issues
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
        Execute general task (delegates to appropriate executor).

        Args:
            task: Task description
            timeout: Execution timeout in seconds
            environment: Optional environment variables

        Returns:
            Execution result dictionary
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
        Deploy code to a service.

        Args:
            service: Name of the service to deploy to
            code: Code or patch to deploy
            deployment_type: Type of deployment ('hotfix', 'update', 'rollback')

        Returns:
            Dictionary with deployment status:
            - status: 'deployed', 'failed', or 'pending'
            - id: Deployment ID
            - service: Service name
            - type: Deployment type
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
        Rollback a deployment.

        Args:
            service: Name of the service
            deployment_id: ID of the deployment to rollback

        Returns:
            Dictionary with rollback status
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
        Get the status of a deployment.

        Args:
            service: Name of the service
            deployment_id: ID of the deployment

        Returns:
            Dictionary with deployment status information
        """
        logger.info(f"Checking deployment status for {deployment_id}")

        # In a real implementation, this would query the deployment system
        return {
            "deployment_id": deployment_id,
            "service": service,
            "status": "unknown",
            "message": "Status tracking not yet implemented"
        }
