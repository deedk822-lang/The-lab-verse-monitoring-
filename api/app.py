from fastapi import FastAPI
from contextlib import asynccontextmanager
from rainmaker_orchestrator.orchestrator import RainmakerOrchestrator

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    orchestrator = RainmakerOrchestrator()
    app.state.orchestrator = orchestrator
    yield
    # Shutdown
    await orchestrator.aclose()

app = FastAPI(title="Rainmaker Orchestrator API", lifespan=lifespan)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
