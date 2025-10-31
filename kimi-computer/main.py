import asyncio
import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

import httpx
import chromadb
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr, Field, validator
from pydantic_settings import BaseSettings

# Structured logging setup
logging.basicConfig(
level=logging.INFO,
format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
class Settings(BaseSettings):
ollama_host: str = "http://ollama:11434"
chromadb_host: str = "chromadb"
chromadb_port: int = 8000
ayr_key: Optional[str] = None
make_webhook: Optional[str] = None
brave_verification_token: Optional[str] = None
log_level: str = "INFO"

class Config:
env_file = ".env"

settings = Settings()

# Pydantic models
class GenerateRequest(BaseModel):
    prompt: str = Field(..., description="Prompt for content generation")
    model: str = Field("mistral", description="Model to use for generation")
    max_tokens: int = Field(1000, description="Maximum tokens to generate")
    temperature: float = Field(0.7, description="Generation temperature")

class GenerateResponse(BaseModel):
    content: str = Field(..., description="Generated content")
    model: str = Field(..., description="Model used for generation")

class ConversionRequest(BaseModel):
utm_source: str = Field(..., description="UTM source parameter")
utm_campaign: Optional[str] = Field(None, description="UTM campaign parameter")
utm_content: Optional[str] = Field(None, description="UTM content parameter")
utm_medium: Optional[str] = Field(None, description="UTM medium parameter")
email: Optional[EmailStr] = Field(None, description="User email address")
name: Optional[str] = Field(None, description="User name")
phone: Optional[str] = Field(None, description="User phone number")
custom_data: Optional[Dict[str, Any]] = Field(None, description="Additional custom data")

@validator('utm_source')
def validate_utm_source(cls, v):
if not v or len(v.strip()) == 0:
raise ValueError('UTM source is required')
return v.strip().lower()

class ConversionResponse(BaseModel):
conversion_id: str = Field(..., description="Unique conversion identifier")
status: str = Field(..., description="Processing status")
timestamp: datetime = Field(..., description="Conversion timestamp")
next_steps: List[str] = Field(..., description="List of next processing steps")

class HealthResponse(BaseModel):
status: str = Field(..., description="Service health status")
model: str = Field(..., description="AI model in use")
uptime: int = Field(..., description="Service uptime in seconds")
memory_usage: Dict[str, float] = Field(..., description="Memory usage information")
services: Dict[str, str] = Field(..., description="Status of dependent services")

# FastAPI app initialization
app = FastAPI(
title="Kimi Computer API",
description="AI-powered social media automation system with BAT monetization",
version="1.0.0",
docs_url="/docs",
redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
CORSMiddleware,
allow_origins=["*"],
allow_credentials=True,
allow_methods=["*"],
allow_headers=["*"],
)

# Global variables
start_time = time.time()

# ChromaDB client initialization
try:
    chroma_client = chromadb.HttpClient(host=settings.chromadb_host, port=settings.chromadb_port)
    collection = chroma_client.get_or_create_collection(name="kimi-computer-content")
    logger.info("ChromaDB client initialized and collection is ready.")
except Exception as e:
    logger.error(f"Failed to initialize ChromaDB client: {e}")
    chroma_client = None
    collection = None

async def check_ollama_health() -> bool:
"""Check if Ollama service is healthy and model is available"""
try:
async with httpx.AsyncClient(timeout=10.0) as client:
response = await client.get(f"{settings.ollama_host}/api/tags")
if response.status_code == 200:
models = response.json().get("models", [])
return any(model.get("name", "").startswith("mistral") for model in models)
return False
except Exception as e:
logger.error(f"Ollama health check failed: {e}")
return False

async def check_chromadb_health() -> bool:
"""Check if ChromaDB service is healthy"""
try:
async with httpx.AsyncClient(timeout=10.0) as client:
response = await client.get(f"http://{settings.chromadb_host}:{settings.chromadb_port}/api/v1/heartbeat")
return response.status_code == 200
except Exception as e:
logger.error(f"ChromaDB health check failed: {e}")
return False

async def generate_mistral_content(prompt: str, model: str = "mistral") -> str:
"""Generate content using Mistral model"""
try:
payload = {
"model": model,
"prompt": prompt,
"stream": False,
"options": {
"temperature": 0.7,
"top_p": 0.9,
"max_tokens": 1000
}
}

async with httpx.AsyncClient(timeout=60.0) as client:
response = await client.post(
f"{settings.ollama_host}/api/generate",
json=payload
)
response.raise_for_status()
result = response.json()
return result.get("response", "").strip()
except Exception as e:
logger.error(f"Mistral generation failed: {e}")
raise HTTPException(status_code=500, detail="Content generation failed")

async def trigger_make_webhook(conversion_data: Dict[str, Any]) -> bool:
"""Trigger Make.com webhook with conversion data"""
if not settings.make_webhook:
logger.warning("Make.com webhook URL not configured")
return False

try:
async with httpx.AsyncClient(timeout=30.0) as client:
response = await client.post(
settings.make_webhook,
json=conversion_data,
headers={"Content-Type": "application/json"}
)
response.raise_for_status()
logger.info(f"Make.com webhook triggered successfully: {response.status_code}")
return True
except Exception as e:
logger.error(f"Make.com webhook trigger failed: {e}")
return False

async def publish_to_ayrshare(content: str, platforms: List[str] = None) -> bool:
"""Publish content to social platforms via Ayrshare"""
if not settings.ayr_key:
logger.warning("Ayrshare API key not configured")
return False

if not platforms:
platforms = ["twitter", "facebook", "linkedin", "instagram"]

try:
payload = {
"post": content,
"platforms": platforms,
"mediaUrls": []
}

headers = {
"Authorization": f"Bearer {settings.ayr_key}",
"Content-Type": "application/json"
}

async with httpx.AsyncClient(timeout=30.0) as client:
response = await client.post(
"https://api.ayrshare.com/api/post",
json=payload,
headers=headers
)
response.raise_for_status()
logger.info(f"Content published via Ayrshare: {response.status_code}")
return True
except Exception as e:
logger.error(f"Ayrshare publishing failed: {e}")
return False

async def process_conversion_background(conversion_id: str, data: Dict[str, Any]):
    """Background processing of conversion data"""
    try:
        logger.info(f"Processing conversion {conversion_id} in background")

        # Generate AI content based on conversion data
        prompt = f"""
        Create a compelling social media post about AI automation and privacy.
        Context: User came from {data.get('utm_source')} campaign "{data.get('utm_campaign')}"
        Make it engaging and include relevant hashtags.
        Keep it under 280 characters for Twitter compatibility.
        """

        ai_content = await generate_mistral_content(prompt)

        # Store content in ChromaDB
        if collection:
            collection.add(
                documents=[ai_content],
                metadatas=[{"source": "conversion", "utm_source": data.get('utm_source')}],
                ids=[conversion_id]
            )
            logger.info(f"Stored content for conversion {conversion_id} in ChromaDB")

        # Publish to social platforms
        await publish_to_ayrshare(ai_content)

        # Log successful processing
        logger.info(f"Conversion {conversion_id} processed successfully")

    except Exception as e:
        logger.error(f"Background processing failed for {conversion_id}: {e}")

@app.get("/health", response_model=HealthResponse)
async def health_check():
"""Health check endpoint with comprehensive system status"""
uptime = int(time.time() - start_time)

# Check dependent services
ollama_healthy = await check_ollama_health()
chromadb_healthy = await check_chromadb_health()

# Get memory usage (simplified)
try:
import psutil
memory = psutil.virtual_memory()
memory_usage = {
"total_gb": round(memory.total / (1024**3), 2),
"available_gb": round(memory.available / (1024**3), 2),
"used_percent": memory.percent
}
except ImportError:
memory_usage = {"total_gb": 0, "available_gb": 0, "used_percent": 0}

services = {
"ollama": "healthy" if ollama_healthy else "unhealthy",
"chromadb": "healthy" if chromadb_healthy else "unhealthy",
"api": "healthy"
}

overall_status = "ok" if all(s == "healthy" for s in services.values()) else "degraded"

return HealthResponse(
status=overall_status,
model="mistral-7b-instruct-v0.3",
uptime=uptime,
memory_usage=memory_usage,
services=services
)

@app.post("/catch", response_model=ConversionResponse)
async def catch_conversion(request: ConversionRequest, background_tasks: BackgroundTasks):
"""Catch and process Brave Ads conversion webhook"""
try:
# Generate unique conversion ID
conversion_id = str(uuid.uuid4())
timestamp = datetime.now(timezone.utc)

# Log conversion
logger.info(f"Received conversion {conversion_id} from {request.utm_source}")

# Prepare conversion data
conversion_data = {
"conversion_id": conversion_id,
"timestamp": timestamp.isoformat(),
"utm_source": request.utm_source,
"utm_campaign": request.utm_campaign,
"utm_content": request.utm_content,
"utm_medium": request.utm_medium,
"email": request.email,
"name": request.name,
"phone": request.phone,
"custom_data": request.custom_data
}

# Trigger Make.com webhook
make_triggered = await trigger_make_webhook(conversion_data)

# Start background processing
background_tasks.add_task(process_conversion_background, conversion_id, conversion_data)

# Determine next steps
next_steps = ["Conversion captured and logged"]
if make_triggered:
next_steps.append("Make.com workflow triggered")
next_steps.append("AI content generation initiated")
next_steps.append("Social media publishing scheduled")

return ConversionResponse(
conversion_id=conversion_id,
status="processed",
timestamp=timestamp,
next_steps=next_steps
)

except Exception as e:
logger.error(f"Conversion processing failed: {e}")
raise HTTPException(status_code=500, detail="Conversion processing failed")

@app.get("/landing", response_class=HTMLResponse)
async def landing_page(request: Request):
"""Landing page with Brave verification meta tag"""
utm_source = request.query_params.get("utm_source", "")
utm_campaign = request.query_params.get("utm_campaign", "")
utm_medium = request.query_params.get("utm_medium", "")

# Brave verification meta tag
brave_meta = ""
if settings.brave_verification_token:
brave_meta = f''

html_content = f"""






{brave_meta}








🚀 Kimi Computer


Your Private AI-Powered Social Media Automation System

Get Started Free








🔒 Privacy First


Run Mistral AI locally with zero data leakage and complete control over your content.






💰 Self-Funding


BAT monetization and affiliate revenue cover your costs while you sleep.






🤖 Always Online


24/7 automated content generation and social media publishing across all platforms.












"""

return HTMLResponse(content=html_content)

@app.post("/generate-content", response_model=GenerateResponse)
async def generate_content(request: GenerateRequest):
    """Generate content using the Mistral model"""
    try:
        content = await generate_mistral_content(
            prompt=request.prompt,
            model=request.model
        )
        return GenerateResponse(content=content, model=request.model)
    except Exception as e:
        logger.error(f"Content generation failed: {e}")
        raise HTTPException(status_code=500, detail="Content generation failed")

class StoreRequest(BaseModel):
    document: str = Field(..., description="Document to store")
    metadata: Dict[str, Any] = Field({}, description="Metadata for the document")
    doc_id: Optional[str] = Field(None, description="Optional document ID")

class QueryRequest(BaseModel):
    query: str = Field(..., description="Query string")
    n_results: int = Field(5, description="Number of results to return")

class QueryResponse(BaseModel):
    results: List[Dict[str, Any]] = Field(..., description="Query results")

@app.post("/store")
async def store_document(request: StoreRequest):
    """Store a document in ChromaDB"""
    if not collection:
        raise HTTPException(status_code=500, detail="ChromaDB not available")
    try:
        doc_id = request.doc_id or str(uuid.uuid4())
        collection.add(
            documents=[request.document],
            metadatas=[request.metadata],
            ids=[doc_id]
        )
        return {"status": "success", "id": doc_id}
    except Exception as e:
        logger.error(f"Failed to store document: {e}")
        raise HTTPException(status_code=500, detail="Failed to store document")

@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """Query documents from ChromaDB"""
    if not collection:
        raise HTTPException(status_code=500, detail="ChromaDB not available")
    try:
        results = collection.query(
            query_texts=[request.query],
            n_results=request.n_results
        )
        return QueryResponse(results=results)
    except Exception as e:
        logger.error(f"Failed to query documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to query documents")

@app.get("/")
async def root():
"""Root endpoint redirecting to documentation"""
return {"message": "Kimi Computer API", "docs": "/docs", "health": "/health"}

if __name__ == "__main__":
import uvicorn
uvicorn.run(app, host="0.0.0.0", port=8080)
