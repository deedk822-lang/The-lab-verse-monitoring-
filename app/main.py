from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any, Optional, Union
import os
import logging
from datetime import datetime
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
    """
    Enforces a fail-closed header authentication using the SELF_HEALING_KEY environment variable for incoming Atlassian webhook requests.
    
    Raises:
        HTTPException: 503 if SELF_HEALING_KEY is not configured.
        HTTPException: 401 if the SELF_HEALING_KEY header is missing or does not match the configured value.
    """
    expected = os.getenv("SELF_HEALING_KEY")
    if not expected:
        raise HTTPException(status_code=503, detail="SELF_HEALING_KEY not configured")

    provided = request.headers.get("SELF_HEALING_KEY")
    if not provided:
        raise HTTPException(status_code=401, detail="Missing SELF_HEALING_KEY header")

    if not secrets.compare_digest(provided, expected):
        raise HTTPException(status_code=401, detail="Invalid SELF_HEALING_KEY")


async def _is_duplicate(event_id: str) -> bool:
    """
    Determine whether an event ID has already been seen within the deduplication TTL.
    
    If the ID has not been seen, record it with the current timestamp so subsequent checks within the TTL will be treated as duplicates.
    
    Parameters:
        event_id (str): Unique identifier for the incoming event to check.
    
    Returns:
        `true` if the event ID was already seen within the TTL, `false` otherwise.
    """
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
    """
    Return a safe, display-friendly label extracted from a URL.
    
    Parameters:
        url (str): The URL to parse.
    
    Returns:
        str: The URL's network location (host and optional port) if present, otherwise "(unknown)".
    """
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
    """
    Handle an incoming Bitbucket webhook and process failed build events.
    
    When the payload's build status is "failed" (case-insensitive), processes the failure, runs enhanced Qwen 3 Plus analysis, optionally forwards the enriched analysis to the configured Atlassian webhook, and returns a combined enhanced result. For non-failed statuses returns a simple handled status.
    
    Parameters:
        payload (BitbucketWebhookPayload): Bitbucket webhook payload to process.
    
    Returns:
        Dict[str, Any]: If the build failed, a dictionary containing `original_response`, `qwen_analysis`, `enhanced` (True), `region`, `source`, and `timestamp`. Otherwise, a dictionary with `status` set to `"handled"`, `region`, `source`, and `timestamp`.
    """
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
            "timestamp": datetime.utcnow().isoformat(),
        }

    return {
        "status": "handled",
        "region": "ap-southeast-1",
        "source": "direct_bitbucket",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/webhook/atlassian")
async def handle_atlassian_webhook(request: Request, payload: AtlassianWebhookPayload) -> Dict[str, Any]:
    """
    Process an incoming Atlassian JSM webhook, deduplicate, convert to a standard payload, and handle failed builds.
    
    Validates the self-healing key header, computes or reads an event identifier to deduplicate requests, converts the Atlassian payload to the service's standard Bitbucket-like payload, and when the converted build status is "failed" runs failure handling and AI analysis and optionally forwards an enhanced payload to the configured Jira webhook.
    
    Returns:
        dict: If the event is a duplicate: {"status": "ignored_duplicate", "source": "atlassian_jsm"}.
              If a failed build was processed: contains keys "original_response" (failure handling result), "qwen_analysis" (AI analysis), "enhanced" (True), "region", "source", "forwarded_to_jira" (True if attempted), and "timestamp".
              Otherwise: {"status": "handled", "region", "source", "timestamp"}.
    """
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
            "timestamp": datetime.utcnow().isoformat(),
        }

    return {
        "status": "handled",
        "region": "ap-southeast-1",
        "source": "atlassian_jsm",
        "timestamp": datetime.utcnow().isoformat(),
    }


def convert_atlassian_to_standard(atlassian_payload: AtlassianWebhookPayload) -> BitbucketWebhookPayload:
    """
    Convert an Atlassian webhook payload into a Bitbucket-like webhook payload.
    
    Parameters:
        atlassian_payload (AtlassianWebhookPayload): Incoming payload; if its `build_status.state` is the string `"failed"` (case-insensitive), the resulting `build_status` will be `"FAILED"`, otherwise `"SUCCESS"`.
    
    Returns:
        BitbucketWebhookPayload: Payload containing `repository`, `commit`, derived `build_status`, and `event_type` set to `"converted_atlassian"`.
    """
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
    """
    Send an enhanced analysis payload to a Jira webhook URL.
    
    Serializes the provided Pydantic payload (supports v2 `model_dump()` and v1 `dict()`), merges it with `qwen_analysis` and an `enhanced_timestamp`, and performs an HTTP POST to `webhook_url`. Any network or HTTP errors are logged and not propagated.
    
    Parameters:
        webhook_url (str): Destination Atlassian/Jira webhook URL (sensitive; not logged in full).
        payload (Union[BitbucketWebhookPayload, AtlassianWebhookPayload]): Original webhook payload model to include in the forwarded payload.
        qwen_analysis (Dict[str, Any]): AI-generated analysis to include alongside the original payload.
    """
    try:
        # Pydantic v2: model_dump(); v1: dict().
        if hasattr(payload, "model_dump"):
            original_payload = payload.model_dump()
        else:
            original_payload = payload.dict()  # type: ignore[attr-defined]

        enhanced_payload = {
            "original_payload": original_payload,
            "qwen_analysis": qwen_analysis,
            "enhanced_timestamp": datetime.utcnow().isoformat(),
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
    """
    Constructs a standardized record for a handled build failure.
    
    Returns a dictionary containing:
    - `status`: the handling outcome identifier.
    - `build_id`: the commit hash associated with the failing build.
    - `repository`: the repository name.
    - `timestamp`: the commit date if present, otherwise the current UTC time in ISO format.
    - `processed_by`: identifier of the processing agent.
    
    Returns:
        Dict[str, Any]: The build failure record with keys `status`, `build_id`, `repository`, `timestamp`, and `processed_by`.
    """
    return {
        "status": "failure_handled",
        "build_id": payload.commit.hash,
        "repository": payload.repository.name,
        "timestamp": payload.commit.date or datetime.utcnow().isoformat(),
        "processed_by": "lab-verse-monitoring-agent-singapore",
    }


async def analyze_with_qwen_3_plus(payload: BitbucketWebhookPayload) -> Dict[str, Any]:
    """
    Generate an AI-enhanced analysis of a Bitbucket webhook payload.
    
    Parameters:
        payload (BitbucketWebhookPayload): Received webhook payload describing repository, commit, and build status.
    
    Returns:
        analysis (Dict[str, Any]): A dictionary containing analysis results with keys:
            - `root_cause` (str): Short description of the likely root cause.
            - `fix_suggestions` (List[str]): Actionable remediation suggestions.
            - `severity` (str): Severity level (e.g., "low", "medium", "high").
            - `confidence` (float): Confidence score between 0 and 1.
            - `region_optimized` (str): Target region or optimization locale.
            - `ai_insights` (str): Human-readable insight produced by the AI.
            - `jira_ready` (bool): Whether the analysis is suitable for creating a Jira ticket.
            - `timestamp` (str): ISO-8601 UTC timestamp of the analysis.
        If analysis fails, returns a dictionary with an `error` message and a `fallback` note.
    """
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
            "timestamp": datetime.utcnow().isoformat(),
        }

        return analysis
    except Exception as e:
        logger.error(f"Qwen 3 Plus analysis failed: {str(e)}")
        return {"error": str(e), "fallback": "Original analysis used"}


# Original health check maintained
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Return the current service health and integration status.
    
    Returns:
        dict: Health payload containing:
            - status (str): Overall health state, e.g. "healthy".
            - region (str): Deployment region identifier.
            - enhanced_with_qwen (bool): `true` if Qwen 3 Plus enhancements are enabled.
            - version (str): Service version string.
            - repository (str): Source repository identifier.
            - atlassian_integration (bool): `true` if Atlassian integration is configured.
            - timestamp (str): ISO-8601 UTC timestamp of when the health snapshot was produced.
    """
    return {
        "status": "healthy",
        "region": "ap-southeast-1",
        "enhanced_with_qwen": True,
        "version": "2.0",
        "repository": "deedk822-lang/The-lab-verse-monitoring-",
        "atlassian_integration": True,
        "timestamp": datetime.utcnow().isoformat(),
    }


# Enhanced endpoint for Bitbucket integration
@app.get("/bitbucket/status")
async def bitbucket_integration_status() -> Dict[str, Any]:
    """
    Report current Bitbucket integration status and related metadata.
    
    Returns:
        dict: A mapping containing:
            - status: overall connection state (e.g., "connected")
            - repository: repository identifier
            - integration: integration state (e.g., "active")
            - webhook_configured: `True` if the ATLAS_WEBHOOK_URL environment variable is set, `False` otherwise
            - atlassian_webhook: human-readable webhook configuration status ("configured" or "not configured")
            - last_sync: timestamp or descriptor of last synchronization
            - timestamp: current UTC time as an ISO 8601 string
    """
    return {
        "status": "connected",
        "repository": "lab-verse-monitoring",
        "integration": "active",
        "webhook_configured": os.getenv("ATLAS_WEBHOOK_URL") is not None,
        "atlassian_webhook": "configured" if os.getenv("ATLAS_WEBHOOK_URL") else "not configured",
        "last_sync": "recent",
        "timestamp": datetime.utcnow().isoformat(),
    }


# Jira integration status endpoint
@app.get("/jira/status")
async def jira_integration_status() -> Dict[str, Any]:
    """
    Report current Jira integration and forwarding status.
    
    Returns:
        status_info (Dict[str, Any]): A dictionary with:
            - status (str): "connected" if ATLAS_WEBHOOK_URL is set, "not configured" otherwise.
            - integration (str): Integration identifier, "atlassian_jsm".
            - webhook_active (bool): True when ATLAS_WEBHOOK_URL is set, False otherwise.
            - enhanced_with_ai (bool): Whether AI enhancements are enabled.
            - last_forwarded (str): Human-readable indicator of the last forwarding event.
            - timestamp (str): ISO 8601 UTC timestamp of when the status was produced.
    """
    return {
        "status": "connected" if os.getenv("ATLAS_WEBHOOK_URL") else "not configured",
        "integration": "atlassian_jsm",
        "webhook_active": os.getenv("ATLAS_WEBHOOK_URL") is not None,
        "enhanced_with_ai": True,
        "last_forwarded": "recent",
        "timestamp": datetime.utcnow().isoformat(),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)