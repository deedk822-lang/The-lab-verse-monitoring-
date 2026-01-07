#!/usr/bin/env python3
"""
agents/background/worker.py
RQ-backed background worker that processes jobs and exposes Prometheus metrics.
- Accepts jobs enqueued by web_worker or scheduler.
- Stores results in Redis under key: job:result:<job_id>
"""
import os
import time
from rq import Queue, Connection, Worker
from redis import Redis
import requests
from agents.agent_base import logger, start_metrics_server, REQUESTS, PROCESS_TIME

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
QUEUE_NAME = os.getenv("QUEUE_NAME", "default")
ALLOW_EXTERNAL = os.getenv("ALLOW_EXTERNAL_REQUESTS", "no").lower() == "yes"

redis_conn = Redis.from_url(REDIS_URL)

def process_http_job(job_payload):
    """
    job_payload is expected to be a dict with:
      - url (required)
      - method (optional, default GET)
      - headers (optional)
      - timeout (optional)
    Returns: dict with status_code, elapsed_ms, content_length
    """
    REQUESTS.inc()
    start = time.time()
    if not isinstance(job_payload, dict):
        return {"error": "invalid payload"}
    url = job_payload.get("url")
    if not url:
        return {"error": "missing url"}

    if not ALLOW_EXTERNAL:
        logger.warning("External requests disabled. Skipping request.", extra={"url": url})
        return {"error": "external requests disabled"}

    method = job_payload.get("method", "GET").upper()
    headers = job_payload.get("headers", {})
    timeout = float(job_payload.get("timeout", 10.0))
    try:
        resp = requests.request(method, url, headers=headers, timeout=timeout)
        result = {
            "status_code": resp.status_code,
            "elapsed_ms": int(resp.elapsed.total_seconds() * 1000),
            "content_length": len(resp.content),
        }
    except Exception as e:
        result = {"error": str(e)}
    elapsed = time.time() - start
    PROCESS_TIME.observe(elapsed)
    return result

def main():
    # Start metrics server
    metrics_port = int(os.getenv("METRICS_PORT", "8001"))
    start_metrics_server(metrics_port)

    logger.info("Starting RQ worker", extra={"redis": REDIS_URL, "queue": QUEUE_NAME})
    with Connection(redis_conn):
        q = Queue(name=QUEUE_NAME, connection=redis_conn, default_timeout=600)
        worker = Worker([q], connection=redis_conn)
        # Register functions that RQ can import and run:
        # The worker expects job func path e.g. "agents.background.worker.process_http_job"
        worker.work(with_scheduler=True)

if __name__ == "__main__":
    main()
