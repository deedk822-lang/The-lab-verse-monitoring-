import os
from flask import Flask, request, jsonify
from orchestrator import RainmakerOrchestrator
import asyncio

app = Flask(__name__)

# Initialize the orchestrator.
# It reads its config from env vars, which are passed by docker-compose.
orchestrator = RainmakerOrchestrator()

@app.route('/execute', methods=['POST'])
def execute_task():
    """Execute a task using the RainmakerOrchestrator."""
    task_data = request.json
    if not task_data:
        return jsonify({"status": "error", "message": "Invalid JSON body"}), 400

    try:
        # Use asyncio.run to execute the async method from a sync context.
        result = asyncio.run(orchestrator.execute_task(task_data))
        return jsonify(result)
    except Exception as e:
        # Log the exception here if you have a logger
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """A simple health check endpoint."""
    return jsonify({"status": "ok"}), 200

# The orchestrator uses an async http client, so we should close it gracefully.
@app.teardown_appcontext
def teardown(exception=None):
    if hasattr(orchestrator, 'aclose'):
        try:
            # Run the async close method.
            asyncio.run(orchestrator.aclose())
        except Exception as e:
            # Log this error
            print(f"Error closing orchestrator client: {e}")


if __name__ == '__main__':
    # This is for local testing without a production WSGI server.
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
