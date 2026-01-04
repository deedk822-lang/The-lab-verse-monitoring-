"""
Lab-Verse Integrated API Server
Connects all platforms with webhooks and sync
"""
import os
import logging
from typing import Dict, Any
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Header, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from redis import asyncio as aioredis

from integrations.manager import get_integration_manager, WebhookValidator
from integrations.connectors import (
    GrafanaConnector,
    HuggingFaceConnector,
    DataDogConnector,
    HubSpotConnector,
    ConfluenceConnector,
    ClickUpConnector,
    CodeRabbitConnector
)

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='{"time":"%(asctime)s", "level":"%(levelname)s", "message":"%(message)s"}'
)
logger = logging.getLogger(__name__)


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    logger.info("Starting Lab-Verse Integrated API Server")

    # Get integration manager
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    manager = await get_integration_manager(redis_url)

    # Initialize Redis for direct access
    app.state.redis = await aioredis.from_url(redis_url, decode_responses=True)

    # Register all platform connectors
    manager.register_connector("grafana", GrafanaConnector(app.state.redis))
    manager.register_connector("huggingface", HuggingFaceConnector(app.state.redis))
    manager.register_connector("datadog", DataDogConnector(app.state.redis))
    manager.register_connector("hubspot", HubSpotConnector(app.state.redis))
    manager.register_connector("confluence", ConfluenceConnector(app.state.redis))
    manager.register_connector("clickup", ClickUpConnector(app.state.redis))
    manager.register_connector("coderabbit", CodeRabbitConnector(app.state.redis))

    app.state.integration_manager = manager

    logger.info("All integrations initialized")

    yield

    # Shutdown
    logger.info("Shutting down Lab-Verse Integrated API Server")
    await manager.close_all()
    await app.state.redis.close()


# Initialize FastAPI app
app = FastAPI(
    title="Lab-Verse Integrated API",
    description="Unified API connecting Grafana, HuggingFace, DataDog, HubSpot, Confluence, ClickUp, CodeRabbit",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class WebhookPayload(BaseModel):
    platform: str
    data: Dict[str, Any]


class SyncRequest(BaseModel):
    platforms: list[str] = []  # Empty means sync all


# Health check endpoint
@app.get("/health")
async def health_check():
    """Overall system health"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0"
    }


@app.get("/health/integrations")
async def integration_health_check():
    """Health status of all integrations"""
    manager = app.state.integration_manager
    health_results = await manager.health_check_all()

    # Convert health objects to dicts
    health_dict = {}
    for platform, health in health_results.items():
        health_dict[platform] = {
            "status": health.status,
            "last_success": health.last_success.isoformat() if health.last_success else None,
            "last_failure": health.last_failure.isoformat() if health.last_failure else None,
            "consecutive_failures": health.consecutive_failures,
            "response_time_ms": health.response_time_ms
        }

    # Overall status
    all_healthy = all(h["status"] == "healthy" for h in health_dict.values())

    return {
        "overall_status": "healthy" if all_healthy else "degraded",
        "integrations": health_dict,
        "timestamp": datetime.utcnow().isoformat()
    }


# ==================== GRAFANA ENDPOINTS ====================

@app.get("/api/grafana/dashboards")
async def get_grafana_dashboards():
    """Get all Grafana dashboards"""
    connector = app.state.integration_manager.get_connector("grafana")
    if not connector:
        raise HTTPException(status_code=503, detail="Grafana integration not available")

    dashboards = await connector.get_dashboards()
    return {"dashboards": dashboards, "count": len(dashboards)}


@app.get("/api/grafana/alerts")
async def get_grafana_alerts():
    """Get Grafana alerts"""
    connector = app.state.integration_manager.get_connector("grafana")
    if not connector:
        raise HTTPException(status_code=503, detail="Grafana integration not available")

    alerts = await connector.get_alerts()
    return {"alerts": alerts, "count": len(alerts)}


@app.post("/webhooks/grafana")
async def grafana_webhook(request: Request):
    """Handle Grafana webhook events"""
    payload = await request.json()

    # Validate webhook (if token provided)
    grafana_token = os.getenv("GRAFANA_WEBHOOK_TOKEN")
    if grafana_token:
        if not WebhookValidator.validate_grafana(payload, grafana_token):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    logger.info(f"Received Grafana webhook: {payload.get('title', 'Unknown')}")

    # Push to Redis queue
    await app.state.redis.lpush("grafana:events", json.dumps(payload))

    return {"status": "accepted"}




# ==================== HUGGING FACE ENDPOINTS ====================

@app.get("/api/huggingface/spaces")
async def get_huggingface_spaces():
    """Get all Hugging Face spaces"""
    connector = app.state.integration_manager.get_connector("huggingface")
    if not connector:
        raise HTTPException(status_code=503, detail="Hugging Face integration not available")

    spaces = await connector.get_spaces()
    return {"spaces": spaces, "count": len(spaces)}


@app.get("/api/huggingface/models")
async def get_huggingface_models():
    """Get all Hugging Face models"""
    connector = app.state.integration_manager.get_connector("huggingface")
    if not connector:
        raise HTTPException(status_code=503, detail="Hugging Face integration not available")

    models = await connector.get_models()
    return {"models": models, "count": len(models)}


# ==================== DATADOG ENDPOINTS ====================

@app.get("/api/datadog/monitors")
async def get_datadog_monitors():
    """Get DataDog monitors"""
    connector = app.state.integration_manager.get_connector("datadog")
    if not connector:
        raise HTTPException(status_code=503, detail="DataDog integration not available")

    monitors = await connector.get_monitors()
    return {"monitors": monitors, "count": len(monitors)}


@app.get("/api/datadog/pipelines")
async def get_datadog_pipelines():
    """Get DataDog CI pipelines"""
    connector = app.state.integration_manager.get_connector("datadog")
    if not connector:
        raise HTTPException(status_code=503, detail="DataDog integration not available")

    pipelines = await connector.get_ci_pipelines()
    return {"pipelines": pipelines}


# ==================== HUBSPOT ENDPOINTS ====================

@app.get("/api/hubspot/contacts")
async def get_hubspot_contacts(limit: int = 100):
    """Get HubSpot contacts"""
    connector = app.state.integration_manager.get_connector("hubspot")
    if not connector:
        raise HTTPException(status_code=503, detail="HubSpot integration not available")

    contacts = await connector.get_contacts(limit)
    return {"contacts": contacts, "count": len(contacts)}


@app.get("/api/hubspot/deals")
async def get_hubspot_deals(limit: int = 100):
    """Get HubSpot deals"""
    connector = app.state.integration_manager.get_connector("hubspot")
    if not connector:
        raise HTTPException(status_code=503, detail="HubSpot integration not available")

    deals = await connector.get_deals(limit)
    return {"deals": deals, "count": len(deals)}


@app.post("/webhooks/hubspot")
async def hubspot_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hubspot_signature: str = Header(None)
):
    """Handle HubSpot webhook events"""
    body = await request.body()

    # Validate webhook signature
    hubspot_secret = os.getenv("HUBSPOT_WEBHOOK_SECRET")
    if hubspot_secret and x_hubspot_signature:
        if not WebhookValidator.validate_hubspot(body, x_hubspot_signature, hubspot_secret):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payload = json.loads(body.decode())
    logger.info(f"Received HubSpot webhook: {payload.get('subscriptionType', 'Unknown')}")

    # Process in background
    background_tasks.add_task(process_hubspot_webhook, payload)

    return {"status": "accepted"}


async def process_hubspot_webhook(payload: Dict[str, Any]):
    """Process HubSpot webhook in background"""
    try:
        event_type = payload.get("subscriptionType")

        # Store event in Redis
        await app.state.redis.lpush(
            "hubspot:events",
            str(payload)
        )
        await app.state.redis.ltrim("hubspot:events", 0, 999)  # Keep last 1000 events

        logger.info(f"Processed HubSpot webhook: {event_type}")
    except Exception as e:
        logger.error(f"Error processing HubSpot webhook: {e}")


# ==================== CONFLUENCE ENDPOINTS ====================

@app.get("/api/confluence/spaces")
async def get_confluence_spaces():
    """Get Confluence spaces"""
    connector = app.state.integration_manager.get_connector("confluence")
    if not connector:
        raise HTTPException(status_code=503, detail="Confluence integration not available")

    spaces = await connector.get_spaces()
    return {"spaces": spaces, "count": len(spaces)}


@app.get("/api/confluence/pages/{space_key}")
async def get_confluence_pages(space_key: str):
    """Get pages in a Confluence space"""
    connector = app.state.integration_manager.get_connector("confluence")
    if not connector:
        raise HTTPException(status_code=503, detail="Confluence integration not available")

    pages = await connector.get_pages(space_key)
    return {"pages": pages, "count": len(pages)}


# ==================== CLICKUP ENDPOINTS ====================

@app.get("/api/clickup/spaces")
async def get_clickup_spaces():
    """Get ClickUp spaces"""
    connector = app.state.integration_manager.get_connector("clickup")
    if not connector:
        raise HTTPException(status_code=503, detail="ClickUp integration not available")

    spaces = await connector.get_spaces()
    return {"spaces": spaces, "count": len(spaces)}


@app.post("/webhooks/clickup")
async def clickup_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_signature: str = Header(None),
    x_timestamp: str = Header(None)
):
    """Handle ClickUp webhook events"""
    body = await request.body()

    # Validate webhook signature
    clickup_secret = os.getenv("CLICKUP_WEBHOOK_SECRET")
    if clickup_secret and x_signature and x_timestamp:
        if not WebhookValidator.validate_clickup(x_signature, clickup_secret, x_timestamp, body.decode()):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payload = json.loads(body)
    logger.info(f"Received ClickUp webhook: {payload.get('event', 'Unknown')}")

    # Process in background
    background_tasks.add_task(process_clickup_webhook, payload)

    return {"status": "accepted"}


async def process_clickup_webhook(payload: Dict[str, Any]):
    """Process ClickUp webhook in background"""
    try:
        event_type = payload.get("event")

        # Store event in Redis
        await app.state.redis.lpush(
            "clickup:events",
            str(payload)
        )
        await app.state.redis.ltrim("clickup:events", 0, 999)

        logger.info(f"Processed ClickUp webhook: {event_type}")
    except Exception as e:
        logger.error(f"Error processing ClickUp webhook: {e}")


# ==================== CODERABBIT ENDPOINTS ====================

@app.get("/api/coderabbit/metrics")
async def get_coderabbit_metrics():
    """Get CodeRabbit review metrics"""
    connector = app.state.integration_manager.get_connector("coderabbit")
    if not connector:
        raise HTTPException(status_code=503, detail="CodeRabbit integration not available")

    metrics = await connector.get_review_metrics()
    quality_score = await connector.get_quality_score()

    return {
        "metrics": metrics,
        "quality_score": quality_score
    }


# ==================== UNIFIED ENDPOINTS ====================

@app.get("/api/dashboard/summary")
async def get_dashboard_summary():
    """Get unified dashboard summary from all platforms"""
    manager = app.state.integration_manager

    summary = {
        "timestamp": datetime.utcnow().isoformat(),
        "platforms": {}
    }

    # Gather data from all platforms
    try:
        # Grafana
        grafana = manager.get_connector("grafana")
        if grafana:
            dashboards = await grafana.get_dashboards()
            alerts = await grafana.get_alerts()
            summary["platforms"]["grafana"] = {
                "dashboards": len(dashboards),
                "active_alerts": len([a for a in alerts if a.get("state") == "alerting"])
            }

        # HubSpot
        hubspot = manager.get_connector("hubspot")
        if hubspot:
            contacts = await hubspot.get_contacts(limit=10)
            deals = await hubspot.get_deals(limit=10)
            summary["platforms"]["hubspot"] = {
                "contacts": len(contacts),
                "deals": len(deals)
            }

        # ClickUp
        clickup = manager.get_connector("clickup")
        if clickup:
            spaces = await clickup.get_spaces()
            summary["platforms"]["clickup"] = {
                "spaces": len(spaces)
            }

        # CodeRabbit
        coderabbit = manager.get_connector("coderabbit")
        if coderabbit:
            quality = await coderabbit.get_quality_score()
            summary["platforms"]["coderabbit"] = {
                "quality_score": quality
            }

    except Exception as e:
        logger.error(f"Error gathering dashboard summary: {e}")

    return summary


@app.post("/api/sync")
async def sync_platforms(sync_request: SyncRequest, background_tasks: BackgroundTasks):
    """Trigger sync for specified platforms (or all if empty)"""
    manager = app.state.integration_manager

    if sync_request.platforms:
        # Sync specific platforms
        for platform in sync_request.platforms:
            connector = manager.get_connector(platform)
            if connector:
                background_tasks.add_task(connector.sync)
    else:
        # Sync all platforms
        background_tasks.add_task(manager.sync_all)

    return {
        "status": "sync_started",
        "platforms": sync_request.platforms or "all",
        "timestamp": datetime.utcnow().isoformat()
    }


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8080)),
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )
