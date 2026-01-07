#!/usr/bin/env python3
"""
agents/agent_base.py
Shared helpers: structured logging, graceful shutdown, Prometheus metrics server.
"""
from pythonjsonlogger import jsonlogger
import logging
import signal
import time
from threading import Event
from prometheus_client import start_http_server, Counter, Histogram

# Structured JSON logging
logger = logging.getLogger("agent_base")
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter('%(asctime)s %(name)s %(levelname)s %(message)s')
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

SHUTDOWN = Event()

# Prometheus metrics (agents should increment these)
REQUESTS = Counter("agent_requests_total", "Total requests handled")
PROCESS_TIME = Histogram("agent_processing_seconds", "Time spent processing a job_seconds")

def handle_signal(signum, frame):
    logger.info("Received signal", extra={"signal": signum})
    SHUTDOWN.set()

for s in (signal.SIGINT, signal.SIGTERM):
    signal.signal(s, handle_signal)

def start_metrics_server(port: int = 8000):
    """Start Prometheus metrics HTTP server on given port"""
    start_http_server(port)
    logger.info("Prometheus metrics server started", extra={"port": port})

def run_loop(poll_interval: float = 1.0):
    """Generic run loop used by simple agents that poll for work."""
    logger.info("Agent run loop starting")
    try:
        while not SHUTDOWN.is_set():
            time.sleep(poll_interval)
    except Exception:
        logger.exception("Unhandled exception in run loop")
    finally:
        logger.info("Agent shutting down gracefully")
