#!/usr/bin/env python3
"""
agents/scheduler/scheduler.py
A small APScheduler-based scheduler that enqueues periodic tasks into the RQ queue.
"""
import os
import time
from redis import Redis
from rq import Queue
from apscheduler.schedulers.background import BackgroundScheduler
from agents.agent_base import logger, start_metrics_server

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
QUEUE_NAME = os.getenv("QUEUE_NAME", "default")
SCHEDULE_INTERVAL_SECONDS = int(os.getenv("SCHEDULE_INTERVAL_SECONDS", "60"))

redis_conn = Redis.from_url(REDIS_URL)
queue = Queue(name=QUEUE_NAME, connection=redis_conn)

def enqueue_health_check():
    """Enqueue a simple job which can be used to validate the pipeline."""
    payload = {"url": "https://httpbin.org/get", "method": "GET", "timeout": 5}
    job = queue.enqueue("agents.background.worker.process_http_job", payload, job_timeout=60)
    logger.info("Scheduled enqueued job", extra={"job_id": job.get_id()})

def main():
    metrics_port = int(os.getenv("METRICS_PORT", "8002"))
    start_metrics_server(metrics_port)
    scheduler = BackgroundScheduler()
    scheduler.add_job(enqueue_health_check, 'interval', seconds=SCHEDULE_INTERVAL_SECONDS, id='health-check')
    scheduler.start()
    logger.info("Scheduler started", extra={"interval_seconds": SCHEDULE_INTERVAL_SECONDS})
    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopping")
        scheduler.shutdown()

if __name__ == "__main__":
    main()
