import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.v1.endpoints import autoglm
from .core.config import settings

# Define a logger
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Add console handler to log messages
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

# Log startup message
logger.info("Starting Rainmaker Orchestrator with GLM-4.7 and AutoGLM integration")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifespan for the FastAPI app.
    
    On startup, prints a startup message; yields control to run the application; on shutdown, prints a shutdown message. This context manager is used by FastAPI to perform any necessary initialization or cleanup.
    """
    try:
        print("Starting Rainmaker Orchestrator with GLM-4.7 and AutoGLM integration")
        # Initialize any resources here
        yield
    except Exception as e:
        logger.error(f"Error starting Rainmaker Orchestrator: {e}")
    finally:
        print("Shutting down Rainmaker Orchestrator")

# Create FastAPI app with lifespan
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Rainmaker Orchestrator with GLM-4.7 and AutoGLM integration",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(autoglm.router, prefix=settings.API_V1_STR)


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
    logger.info("Request received for root endpoint")
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
    logger.info("Request received for health check endpoint")
    return {
        "status": "healthy",
        "service": "rainmaker-orchestrator",
        "version": settings.VERSION,
        "timestamp": time.time()
    }
