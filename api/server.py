from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import sys
import os

# Add the parent directory to the Python path to allow importing the orchestrator
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rainmaker_orchestrator import RainmakerOrchestrator, DirectiveResult

app = FastAPI()
orchestrator = RainmakerOrchestrator()

class DirectiveRequest(BaseModel):
    directive: str
    timeout: int = 120

class BatchRequest(BaseModel):
    directives: List[str]

@app.post("/directive", response_model=DirectiveResult)
async def execute_directive_endpoint(request: DirectiveRequest):
    result = await orchestrator.execute_directive(request.directive)
    return result

@app.post("/batch")
async def batch_execute_endpoint(request: BatchRequest):
    results = await orchestrator.batch_execute(request.directives)
    return {"results": results}

@app.get("/health")
def health_check():
    # A more robust health check would verify connections to downstream services
    return {"status": "healthy"}

@app.get("/tools")
def list_tools():
    # This could be expanded to provide more details about each tool
    return {"tools": sorted(list(set(tool.value for tool in orchestrator.parser.KEYWORDS.values())))}
