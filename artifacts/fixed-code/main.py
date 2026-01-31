from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Rainmaker Orchestrator with GLM-4.7 and AutoGLM integration",
    version="1.0.0",
    description="Rainmaker Orchestrator with GLM-4.7 and AutoGLM integration",
)

# Add CORS middleware
origins = [
    "http://localhost:3000",  # Replace with your actual frontend URL
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
from .api.v1.endpoints import autoglm
app.include_router(autoglm.router, prefix="/v1")

@app.get("/")
async def root():
    return {
        "message": "Rainmaker Orchestrator with GLM-4.7 and AutoGLM Integration",
        "version": "1.0.0",
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
    return {
        "status": "healthy",
        "service": "rainmaker-orchestrator",
        "version": "1.0.0",
        "timestamp": time.time()
    }