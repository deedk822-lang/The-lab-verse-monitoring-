"""
Rainmaker Orchestrator HTTP Server
Flask-based HTTP interface for the async orchestrator
Aligned with actual orchestrator.py implementation
"""
import asyncio
import atexit
import logging
import os
from typing import Dict, Any

from flask import Flask, request, jsonify
from rainmaker_orchestrator.orchestrator import RainmakerOrchestrator
from rainmaker_orchestrator.agents.healer import SelfHealingAgent

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='{"time":"%(asctime)s", "level":"%(levelname)s", "message":"%(message)s", "module":"%(name)s"}'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Create module-level orchestrator instance (singleton)
logger.info("Initializing Rainmaker Orchestrator")
try:
    workspace_path = os.getenv("WORKSPACE_PATH", "/workspace")
    config_file = os.getenv("CONFIG_FILE", ".env")
    orchestrator = RainmakerOrchestrator(
        workspace_path=workspace_path,
        config_file=config_file
    )
    healer = SelfHealingAgent()
    logger.info(f"Orchestrator initialized (workspace: {workspace_path})")
except Exception as e:
    logger.error(f"Failed to initialize orchestrator: {e}", exc_info=True)
    raise


def validate_execute_request(data: Dict[str, Any]) -> tuple[bool, str]:
    """
    Validate the execute request payload.

    Args:
        data: Request JSON data

    Returns:
        Tuple of (is_valid, error_message)
    """
    if data is None:
        return False, "Request body is required"

    # Required fields based on actual orchestrator.py
    if "context" not in data:
        return False, "Missing required field: 'context'"

    context = data.get("context", "")
    if not isinstance(context, str) or not context.strip():
        return False, "Field 'context' must be a non-empty string"

    # Validate optional fields if present
    if "type" in data:
        valid_types = ["coding_task"]  # Based on orchestrator.py
        if data["type"] not in valid_types:
            return False, f"Field 'type' must be one of: {valid_types}"

    if "model" in data and not isinstance(data["model"], str):
        return False, "Field 'model' must be a string"

    if "output_filename" in data:
        filename = data["output_filename"]
        if not isinstance(filename, str) or not filename.strip():
            return False, "Field 'output_filename' must be a non-empty string"
        # Basic security check for filename
        if ".." in filename or "/" in filename or "\\" in filename:
            return False, "Field 'output_filename' contains invalid characters"

    return True, ""


@app.route("/webhook/alert", methods=["POST"])
def handle_alert():
    """
    Handle alerts from Prometheus Alert Manager.
    """
    try:
        alert_payload = request.get_json()
        logger.info(f"Received alert: {alert_payload}")
        result = healer.handle_alert(alert_payload)
        return jsonify({"status": "success", "result": result}), 200
    except Exception as e:
        logger.error(f"Failed to handle alert: {e}", exc_info=True)
        return jsonify({"error": "Failed to handle alert", "details": str(e)}), 500


@app.route("/execute", methods=["POST"])
def execute_task():
    """
    Execute a task via the orchestrator.

    Expected JSON payload:
    {
        "context": "description of task or prompt",
        "type": "coding_task" (optional),
        "model": "kimi" or "ollama" (optional),
        "output_filename": "script.py" (optional, required for coding_task)
    }

    Returns:
        JSON response with result or error
    """
    request_id = request.headers.get("X-Request-ID", "unknown")

    try:
        # Parse and validate request
        data = request.get_json(silent=True)

        is_valid, error_msg = validate_execute_request(data)
        if not is_valid:
            logger.warning(f"Invalid request [{request_id}]: {error_msg}")
            return jsonify({
                "error": error_msg,
                "status": "invalid_request"
            }), 400

        # Build task dict for orchestrator
        task = {
            "context": data["context"],
            "type": data.get("type"),
            "model": data.get("model"),
            "output_filename": data.get("output_filename")
        }

        # Log task details
        task_type = task.get("type", "general")
        logger.info(f"Executing {task_type} task [{request_id}]")

        # Execute async task in a new event loop
        # This is safe because Flask+Gunicorn runs each request in its own thread
        result = asyncio.run(orchestrator.execute_task(task))

        # Check result status
        if result.get("status") == "success":
            logger.info(f"Task completed successfully [{request_id}]")
            return jsonify({
                "result": result,
                "status": "success",
                "request_id": request_id
            }), 200

        elif result.get("status") == "failed":
            logger.warning(f"Task failed [{request_id}]: {result.get('message', 'Unknown error')}")
            return jsonify({
                "error": result.get("message", "Task execution failed"),
                "details": result,
                "status": "failed",
                "request_id": request_id
            }), 422  # Unprocessable Entity

        else:
            logger.error(f"Task error [{request_id}]: {result.get('message', 'Unknown error')}")
            return jsonify({
                "error": result.get("message", "Task execution error"),
                "details": result,
                "status": "error",
                "request_id": request_id
            }), 500

    except asyncio.TimeoutError:
        logger.error(f"Task timeout [{request_id}]")
        return jsonify({
            "error": "Task execution timed out",
            "status": "timeout",
            "request_id": request_id
        }), 504

    except ValueError as e:
        logger.warning(f"Validation error [{request_id}]: {e}")
        return jsonify({
            "error": str(e),
            "status": "validation_error",
            "request_id": request_id
        }), 400

    except Exception as e:
        logger.error(f"Task execution failed [{request_id}]: {e}", exc_info=True)
        return jsonify({
            "error": "Internal server error during task execution",
            "details": str(e),
            "status": "error",
            "request_id": request_id
        }), 500


@app.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint for container orchestration.

    Returns:
        JSON response with health status
    """
    try:
        # Check if orchestrator is initialized
        if orchestrator is None:
            return jsonify({
                "status": "unhealthy",
                "reason": "Orchestrator not initialized"
            }), 503

        # Check required configuration
        missing_keys = orchestrator.config.validate(["KIMI_API_KEY"])

        if missing_keys:
            logger.warning(f"Missing configuration keys: {missing_keys}")
            return jsonify({
                "status": "degraded",
                "reason": f"Missing configuration: {', '.join(missing_keys)}",
                "service": "rainmaker-orchestrator",
                "version": "2.0.0"
            }), 200  # Still return 200 so container doesn't restart

        # Check workspace accessibility
        try:
            workspace = orchestrator.fs.workspace
            if not os.path.exists(workspace):
                os.makedirs(workspace, exist_ok=True)
            if not os.access(workspace, os.W_OK):
                raise PermissionError("Workspace not writable")
        except Exception as e:
            logger.error(f"Workspace check failed: {e}")
            return jsonify({
                "status": "degraded",
                "reason": f"Workspace issue: {str(e)}",
                "service": "rainmaker-orchestrator",
                "version": "2.0.0"
            }), 200

        # All checks passed
        return jsonify({
            "status": "healthy",
            "service": "rainmaker-orchestrator",
            "version": "2.0.0",
            "workspace": orchestrator.fs.workspace,
            "configured_models": ["kimi", "ollama"]
        }), 200

    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return jsonify({
            "status": "unhealthy",
            "reason": str(e)
        }), 503


@app.route("/workspace/files", methods=["GET"])
def list_workspace_files():
    """
    List files in the workspace.

    Returns:
        JSON response with file list
    """
    try:
        workspace = orchestrator.fs.workspace
        if not os.path.exists(workspace):
            return jsonify({
                "files": [],
                "workspace": workspace
            }), 200

        files = []
        for filename in os.listdir(workspace):
            filepath = os.path.join(workspace, filename)
            if os.path.isfile(filepath):
                stat = os.stat(filepath)
                files.append({
                    "name": filename,
                    "size": stat.st_size,
                    "modified": stat.st_mtime
                })

        return jsonify({
            "files": files,
            "count": len(files),
            "workspace": workspace
        }), 200

    except Exception as e:
        logger.error(f"Failed to list workspace files: {e}", exc_info=True)
        return jsonify({
            "error": "Failed to list workspace files",
            "details": str(e)
        }), 500


@app.route("/workspace/files/<filename>", methods=["GET"])
def get_workspace_file(filename):
    """
    Get content of a workspace file.

    Args:
        filename: Name of file to retrieve

    Returns:
        JSON response with file content
    """
    try:
        result = orchestrator.fs.read_file(filename)

        if result["status"] == "success":
            return jsonify({
                "filename": filename,
                "content": result["content"],
                "status": "success"
            }), 200
        else:
            return jsonify({
                "error": result["message"],
                "status": result["status"]
            }), 404 if "not found" in result["message"].lower() else 500

    except Exception as e:
        logger.error(f"Failed to read file {filename}: {e}", exc_info=True)
        return jsonify({
            "error": "Failed to read file",
            "details": str(e)
        }), 500


@app.route("/metrics", methods=["GET"])
def metrics():
    """
    Prometheus-compatible metrics endpoint.

    Returns:
        Text response with metrics in Prometheus format
    """
    # This is a placeholder - implement actual metrics collection
    # You could track: requests_total, errors_total, task_duration, etc.
    metrics_text = """# HELP orchestrator_requests_total Total number of requests
# TYPE orchestrator_requests_total counter
orchestrator_requests_total 0

# HELP orchestrator_errors_total Total number of errors
# TYPE orchestrator_errors_total counter
orchestrator_errors_total 0

# HELP orchestrator_tasks_total Total number of tasks executed
# TYPE orchestrator_tasks_total counter
orchestrator_tasks_total 0
"""
    return metrics_text, 200, {"Content-Type": "text/plain; charset=utf-8"}


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        "error": "Endpoint not found",
        "status": "not_found",
        "available_endpoints": [
            "POST /execute",
            "GET /health",
            "GET /workspace/files",
            "GET /workspace/files/<filename>",
            "GET /metrics"
        ]
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors"""
    return jsonify({
        "error": "Method not allowed",
        "status": "method_not_allowed"
    }), 405


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}", exc_info=True)
    return jsonify({
        "error": "Internal server error",
        "status": "error"
    }), 500


def cleanup_orchestrator():
    """
    Clean up orchestrator resources on process exit.
    This runs when the process terminates, not after each request.
    """
    logger.info("Shutting down orchestrator...")
    try:
        if hasattr(orchestrator, 'aclose'):
            # Create a new event loop for cleanup
            # (the main loop may already be closed)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(orchestrator.aclose())
                logger.info("Orchestrator HTTP client closed successfully")
            finally:
                loop.close()
    except Exception as e:
        logger.error(f"Error during orchestrator cleanup: {e}", exc_info=True)


# Register cleanup function to run on process exit (NOT per-request!)
atexit.register(cleanup_orchestrator)


# Only run development server if this file is executed directly
if __name__ == "__main__":
    logger.info("Starting development server (not for production!)")
    logger.warning("Use Gunicorn for production: gunicorn --bind 0.0.0.0:8080 server:app")
    app.run(
        host="0.0.0.0",
        port=8080,
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true"
    )