#!/usr/bin/env python3
"""
agents/frontend/web_worker.py
FastAPI app that accepts jobs and enqueues them to Redis/RQ.
Provides:
 - POST /jobs -> enqueue job (returns job id)
 - GET /jobs/{job_id} -> job status & result
 - GET /health -> simple health check
 - /metrics -> Prometheus metrics endpoint
"""
import os
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field
from typing import Dict
from redis import Redis
from rq import Queue
import rq
from agents.agent_base import start_metrics_server, logger
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
QUEUE_NAME = os.getenv("QUEUE_NAME", "default")
METRICS_PORT = int(os.getenv("METRICS_PORT", "8000"))

redis_conn = Redis.from_url(REDIS_URL)
queue = Queue(name=QUEUE_NAME, connection=redis_conn)

REQUESTS = Counter("web_enqueue_requests_total", "Total enqueue requests")
ENQUEUE_LATENCY = Histogram("web_enqueue_seconds", "Time to enqueue a job")

app = FastAPI(title="Agent Web Worker")

class JobPayload(BaseModel):
    url: str
    method: str = "GET"
    headers: Dict[str, str] = Field(default_factory=dict)
    timeout: float = 10.0

@app.on_event("startup")
def startup():
    # Start metrics server on separate port for prometheus scraping (used by background worker as well)
    start_metrics_server(METRICS_PORT)
    logger.info("web_worker startup complete", extra={"redis": REDIS_URL, "queue": QUEUE_NAME})

@app.post("/jobs")
def create_job(payload: JobPayload):
    REQUESTS.inc()
    with ENQUEUE_LATENCY.time():
        # Enqueue the background worker function (must reference the importable path)
        job = queue.enqueue(
            "agents.background.worker.process_http_job",
            payload.dict(),
            job_timeout=600,
            retry=rq.Retry(max=2, interval=[10, 30]),
        )
    return {"job_id": job.get_id(), "enqueued_at": str(job.enqueued_at)}

@app.get("/jobs/{job_id}")
def job_status(job_id: str):
    try:
        job = rq.job.Job.fetch(job_id, connection=redis_conn)
    except rq.exceptions.NoSuchJobError:
        raise HTTPException(status_code=404, detail="job not found") from None
    response = {
        "id": job.get_id(),
        "status": job.get_status(),
        "result": job.result,
        "enqueued_at": str(job.enqueued_at),
        "started_at": str(job.started_at) if getattr(job, "started_at", None) else None,
        "ended_at": str(job.ended_at) if getattr(job, "ended_at", None) else None,
    }
    if job.exc_info:
        response["error"] = "internal error"
    return response

@app.get("/health")
def health():
    # Basic checks: Redis reachable and RQ queue accessible
    try:
        redis_conn.ping()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"redis unreachable: {e}")
    return {"status": "ok"}

@app.get("/metrics")
def metrics():
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("agents.frontend.web_worker:app", host="0.0.0.0", port=8080, log_level="info")
