# api/server.py - FIXED
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import sys
import os

# ✅ DO NOT use sys.path.append - use PYTHONPATH environment variable instead
# This should be set in Dockerfile: ENV PYTHONPATH=/app:$PYTHONPATH

# ✅ Improved import with error handling
try:
    from rainmaker_orchestrator import RainmakerOrchestrator, DirectiveResult
    print("✅ Successfully imported rainmaker_orchestrator")
except ImportError as e:
    print(f"❌ CRITICAL: Failed to import rainmaker_orchestrator: {e}")
    print(f"Python path: {sys.path}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Directory contents: {os.listdir('.')}")
    raise SystemExit(1)  # Fail fast

app = FastAPI(
    title="Rainmaker API",
    version="1.0.0",
    description="AI Orchestration API"
)

orchestrator = RainmakerOrchestrator()

class DirectiveRequest(BaseModel):
    directive: str
    context: dict = {}

@app.get("/health")
async def health_check():
    """
    ✅ Enhanced health check - verify downstream services
    """
    health_status = {
        "status": "healthy",
        "services": {}
    }

    try:
        # Check if orchestrator is responsive
        tools = orchestrator.parser.KEYWORDS
        health_status["services"]["orchestrator"] = "healthy"
        health_status["services"]["available_tools"] = len(set(tools.values()))
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["services"]["orchestrator"] = f"unhealthy: {str(e)}"

    # Return appropriate status code
    status_code = 200 if health_status["status"] == "healthy" else 503

    return health_status

@app.get("/tools")
def list_tools():
    """List all available tools"""
    try:
        tools = sorted(list(set(
            tool.value for tool in orchestrator.parser.KEYWORDS.values()
        )))
        return {"tools": tools, "count": len(tools)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/directive")
async def process_directive(request: DirectiveRequest):
    """Process a directive through the orchestrator"""
    try:
        result = await orchestrator.process(request.directive, request.context)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
