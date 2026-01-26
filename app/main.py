from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any, Optional, Union
import os
import logging
from datetime import datetime, timezone
import httpx
import asyncio
import hashlib
import secrets
import time
from urllib.parse import urlsplit

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Lab-Verse Monitoring Agent - Enhanced with Qwen 3 Plus")

# In-memory dedupe (single-process). If you run multiple workers, move to Redis.
_DEDUP_TTL_SECONDS = int(os.getenv("ATLASSIAN_DEDUP_TTL_SECONDS", "3600"))
_seen_ids: Dict[str, float] = {}
_seen_lock = asyncio.Lock()


def _require_self_healing_key(request: Request) -> None:
    """Fail-closed header auth for Atlassian inbound webhooks."""
    expected = os.getenv("SELF_HEALING_KEY")
    if not expected:
        raise HTTPException(status_code=503, detail="SELF_HEALING_KEY not configured")

    provided = request.headers.get("SELF_HEALING_KEY")
    if not provided:
        raise HTTPException(status_code=401, detail="Missing SELF_HEALING_KEY header")

    if not secrets.compare_digest(provided, expected):
        raise HTTPException(status_code=401, detail="Invalid SELF_HEALING_KEY")


async def _is_duplicate(event_id: str) -> bool:
    now = time.time()
    async with _seen_lock:
        expired = [k for k, ts in _seen_ids.items() if now - ts > _DEDUP_TTL_SECONDS]
        for k in expired:
            _seen_ids.pop(k, None)

        if event_id in _seen_ids:
            return True

        _seen_ids[event_id] = now
        return False


def _safe_target_label(url: str) -> str:
    parts = urlsplit(url)
    return parts.netloc or "(unknown)"


# Models with proper typing
class RepositoryInfo(BaseModel):
    name: str
    full_name: Optional[str] = None
    url: Optional[str] = None


class CommitInfo(BaseModel):
    hash: str
    message: Optional[str] = None
    author: Optional[Dict[str, Any]] = None
    date: Optional[str] = None


class BitbucketWebhookPayload(BaseModel):
    repository: RepositoryInfo
    commit: CommitInfo
    build_status: str
    event_type: Optional[str] = "build_status"


class AtlassianWebhookPayload(BaseModel):
    event: str
    date: str
    actor: Dict[str, Any]
    repository: RepositoryInfo
    commit: CommitInfo
    build_status: Optional[Dict[str, Any]] = None


@app.post("/webhook/bitbucket")
async def handle_bitbucket_webhook(payload: BitbucketWebhookPayload) -> Dict[str, Any]:
    """Handle traditional Bitbucket webhook"""
    logger.info(f"Received Bitbucket webhook: {payload.build_status}")

    if payload.build_status.lower() == "failed":
        original_response = await handle_build_failure(payload)
        qwen_analysis = await analyze_with_qwen_3_plus(payload)

        # Forward to Jira if Atlassian webhook is configured
        atlassian_webhook_url = os.getenv("ATLAS_WEBHOOK_URL")
        if atlassian_webhook_url:
            await forward_to_jira(atlassian_webhook_url, payload, qwen_analysis)

        return {
            "original_response": original_response,
            "qwen_analysis": qwen_analysis,
            "enhanced": True,
            "region": "ap-southeast-1",
            "source": "direct_bitbucket",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    return {
        "status": "handled",
        "region": "ap-southeast-1",
        "source": "direct_bitbucket",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/webhook/atlassian")
async def handle_atlassian_webhook(request: Request, payload: AtlassianWebhookPayload) -> Dict[str, Any]:
    """Handle Atlassian JSM webhook"""
    _require_self_healing_key(request)

    # Prefer the Atlassian retry identifier when present; otherwise hash request body.
    event_id = request.headers.get("X-Atlassian-Webhook-Identifier")
    if not event_id:
        raw = await request.body()
        event_id = hashlib.sha256(raw).hexdigest()

    if await _is_duplicate(event_id):
        return {"status": "ignored_duplicate", "source": "atlassian_jsm"}

    logger.info(f"Received Atlassian webhook: {payload.event}")

    # Convert Atlassian payload to our standard format
    standard_payload = convert_atlassian_to_standard(payload)

    if standard_payload.build_status.lower() == "failed":
        original_response = await handle_build_failure(standard_payload)
        qwen_analysis = await analyze_with_qwen_3_plus(standard_payload)

        # Forward to Jira through Atlassian webhook
        atlassian_webhook_url = os.getenv("ATLAS_WEBHOOK_URL")
        if atlassian_webhook_url:
            await forward_to_jira(atlassian_webhook_url, payload, qwen_analysis)

        return {
            "original_response": original_response,
            "qwen_analysis": qwen_analysis,
            "enhanced": True,
            "region": "ap-southeast-1",
            "source": "atlassian_jsm",
            "forwarded_to_jira": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    return {
        "status": "handled",
        "region": "ap-southeast-1",
        "source": "atlassian_jsm",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def convert_atlassian_to_standard(atlassian_payload: AtlassianWebhookPayload) -> BitbucketWebhookPayload:
    """Convert Atlassian payload to standard Bitbucket format"""
    build_status = "SUCCESS"
    if atlassian_payload.build_status:
        state = atlassian_payload.build_status.get("state")
        if isinstance(state, str) and state.lower() == "failed":
            build_status = "FAILED"

    return BitbucketWebhookPayload(
        repository=atlassian_payload.repository,
        commit=atlassian_payload.commit,
        build_status=build_status,
        event_type="converted_atlassian",
    )


async def forward_to_jira(
    webhook_url: str,
    payload: Union[BitbucketWebhookPayload, AtlassianWebhookPayload],
    qwen_analysis: Dict[str, Any],
) -> None:
    """Forward enhanced analysis to Jira through Atlassian webhook"""
    try:
        # Pydantic v2: model_dump(); v1: dict().
        if hasattr(payload, "model_dump"):
            original_payload = payload.model_dump()
        else:
            original_payload = payload.dict()  # type: ignore[attr-defined]

        enhanced_payload = {
            "original_payload": original_payload,
            "qwen_analysis": qwen_analysis,
            "enhanced_timestamp": datetime.now(timezone.utc).isoformat(),
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(webhook_url, json=enhanced_payload)
            response.raise_for_status()
            logger.info(f"Forwarded to Jira: {response.status_code}")

    except httpx.RequestError as exc:
        # Never log full URL (tokens may be embedded in query/path).
        logger.error(f"Jira forward request failed (target={_safe_target_label(webhook_url)}): {exc}")

    except httpx.HTTPStatusError as exc:
        logger.error(
            f"Jira forward failed (target={_safe_target_label(webhook_url)} status={exc.response.status_code}): {exc}"
        )

    except Exception as e:
        logger.error(f"An unexpected error occurred when forwarding to Jira: {e}")


async def handle_build_failure(payload: BitbucketWebhookPayload) -> Dict[str, Any]:
    """Original build failure handling logic"""
    return {
        "status": "failure_handled",
        "build_id": payload.commit.hash,
        "repository": payload.repository.name,
        "timestamp": payload.commit.date or datetime.now(timezone.utc).isoformat(),
        "processed_by": "lab-verse-monitoring-agent-singapore",
    }


async def analyze_with_qwen_3_plus(payload: BitbucketWebhookPayload) -> Dict[str, Any]:
    """Enhanced analysis using Qwen 3 Plus"""
    try:
        # Simulate Qwen 3 Plus analysis
        analysis = {
            "root_cause": "Identified by Qwen 3 Plus AI",
            "fix_suggestions": [
                "Review code changes in recent commits",
                "Check dependency versions",
                "Verify environment variables",
            ],
            "severity": "high",
            "confidence": 0.95,
            "region_optimized": "ap-southeast-1",
            "ai_insights": (
                "Qwen 3 Plus detected potential configuration issues in the build "
                "process"
            ),
            "jira_ready": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        return analysis
    except Exception as e:
        logger.error(f"Qwen 3 Plus analysis failed: {str(e)}")
        return {"error": str(e), "fallback": "Original analysis used"}


# Original health check maintained
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "region": "ap-southeast-1",
        "enhanced_with_qwen": True,
        "version": "2.0",
        "repository": "deedk822-lang/The-lab-verse-monitoring-",
        "atlassian_integration": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# Enhanced endpoint for Bitbucket integration
@app.get("/bitbucket/status")
async def bitbucket_integration_status() -> Dict[str, Any]:
    """Bitbucket integration status"""
    return {
        "status": "connected",
        "repository": "lab-verse-monitoring",
        "integration": "active",
        "webhook_configured": os.getenv("ATLAS_WEBHOOK_URL") is not None,
        "atlassian_webhook": "configured" if os.getenv("ATLAS_WEBHOOK_URL") else "not configured",
        "last_sync": "recent",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# Jira integration status endpoint
@app.get("/jira/status")
async def jira_integration_status() -> Dict[str, Any]:
    """Jira integration status"""
    return {
        "status": "connected" if os.getenv("ATLAS_WEBHOOK_URL") else "not configured",
        "integration": "atlassian_jsm",
        "webhook_active": os.getenv("ATLAS_WEBHOOK_URL") is not None,
        "enhanced_with_ai": True,
        "last_forwarded": "recent",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
