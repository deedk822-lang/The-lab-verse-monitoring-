from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.v1.endpoints import autoglm
from .core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    """
    print("Starting Rainmaker Orchestrator with GLM-4.7 and AutoGLM integration")
    # Initialize any resources here
    yield
    print("Shutting down Rainmaker Orchestrator")
    # Cleanup resources here


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
    """Root endpoint"""
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
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "rainmaker-orchestrator",
        "version": settings.VERSION,
        "timestamp": 1234567890
    }
