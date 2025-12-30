from fastapi import FastAPI
import sys
import os

# Ensure the root directory is in sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from rainmaker_orchestrator import RainmakerOrchestrator
    print(f"✅ Successfully imported rainmaker_orchestrator in server")
except ImportError as e:
    print(f"❌ Import error in server: {e}")
    print(f"CWD: {os.getcwd()}")
    raise

app = FastAPI(title="Lab Verse API")
orchestrator = RainmakerOrchestrator()

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
