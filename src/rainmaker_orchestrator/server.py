import asyncio
import logging
import os
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from .orchestrator import RainmakerOrchestrator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Rainmaker Orchestrator API")
orchestrator = RainmakerOrchestrator()

class TaskRequest(BaseModel):
    task: str
    context: Optional[Dict[str, Any]] = None

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0 (FastAPI)"}

@app.post("/execute")
async def execute_task(request: TaskRequest, background_tasks: BackgroundTasks):
    try:
        # For long-running tasks, we might want to use background_tasks
        # but for now, we'll execute directly
        result = await orchestrator.execute(request.task, request.context)
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"Task execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
