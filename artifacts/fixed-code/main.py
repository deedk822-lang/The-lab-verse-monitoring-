import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPBasicCredentials, Security
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Define a simple user model for authentication
class User(BaseModel):
    username: str
    password: str

# Initialize the app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Rainmaker Orchestrator with GLM-4.7 and AutoGLM integration",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define a basic HTTP authentication scheme
def get_current_user(credentials: HTTPBasicCredentials = Depends(Security(HTTPBasicCredentials))):
    user = User(username=credentials.username, password=credentials.password)
    # Replace this with actual authentication logic (e.g., checking against a database)
    if user.username == "admin" and user.password == "password":  # Example hardcoded credentials
        return user
    raise HTTPException(status_code=401, detail="Incorrect username or password")

# Include the autoglm router with authentication
app.include_router(autoglm.router, prefix=settings.API_V1_STR, dependencies=[Security(get_current_user)])

@app.get("/")
async def root():
    """
    Provide application metadata and a list of supported features.
    
    Returns:
        dict: A mapping with keys:
            - "message": Human-readable description of the application.
            - "version": Application version string from configuration.
            - "features": List of feature description strings.
    """
    return {
        "message": "Rainmaker Orchestrator with GLM-4.7 and AutoGLM Integration",
        "version": settings.VERSION,
        "features": [
            "GLM-4.7 advanced reasoning",
            "AutoGLM autonomous orchestration",
            "Alibaba Cloud security integration",
            "Multi-AI provider support",
            "Multi-tenant architecture",
            "Rate limiting and security controls"
        ]
    }

@app.get("/health")
async def health_check():
    """
    Provide runtime health information for the Rainmaker Orchestrator service.
    
    Returns:
        dict: Health payload containing:
            - status (str): service health status, e.g. "healthy".
            - service (str): service identifier, "rainmaker-orchestrator".
            - version (str): application version from settings.VERSION.
            - timestamp (float): current Unix time in seconds.
    """
    return {
        "status": "healthy",
        "service": "rainmaker-orchestrator",
        "version": settings.VERSION,
        "timestamp": time.time()
    }