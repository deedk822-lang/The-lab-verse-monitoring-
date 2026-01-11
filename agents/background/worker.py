#!/usr/bin/env python3
"""
agents/background/worker.py
RQ-backed background worker that processes jobs and exposes Prometheus metrics.
- Accepts jobs enqueued by web_worker or scheduler.
- Stores results in Redis under key: job:result:<job_id>
"""
import os
import time
import socket
import ipaddress
from urllib.parse import urlparse
from collections import defaultdict
from time import time as current_time

from rq import Queue, Worker
from redis import Redis
from redis.exceptions import RedisError
import requests
from prometheus_client import Counter

from agents.agent_base import logger, start_metrics_server, REQUESTS, PROCESS_TIME

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
QUEUE_NAME = os.getenv("QUEUE_NAME", "default")
ALLOW_EXTERNAL = os.getenv("ALLOW_EXTERNAL_REQUESTS", "no").lower() == "yes"
MAX_TIMEOUT = 30.0
MAX_CONTENT_SIZE = 10 * 1024 * 1024  # 10MB max

redis_conn = Redis.from_url(REDIS_URL)

SSRF_BLOCKS = Counter(
    'ssrf_blocked_requests_total',
    'Total SSRF attempts blocked',
    ['reason', 'hostname']
)

def check_rate_limit(client_id: str, limit: int = 100, window: int = 60) -> bool:
    """
    Enforce a distributed per-client rate limit using Redis.
    
    Increments a Redis counter keyed by the provided client identifier and sets a TTL equal to the window on the counter's first increment. If the counter exceeds the limit, the request is disallowed. If Redis is unavailable or an error occurs, the function fails open and allows the request.
    
    Parameters:
        client_id (str): Identifier used as the Redis key for rate limiting.
        limit (int): Maximum allowed requests within the window.
        window (int): Time window in seconds for counting requests.
    
    Returns:
        bool: `True` if the request is allowed, `False` if the rate limit has been exceeded.
    """
    if not redis_conn:
        logger.critical("Redis connection missing. Failing open for safety.")
        return True

    key = f"rate_limit:{client_id}"
    try:
        current_count = redis_conn.incr(key)
        if current_count == 1 or redis_conn.ttl(key) == -1:
            redis_conn.expire(key, window)
        if current_count > limit:
            logger.warning(f"Rate limit exceeded for {client_id}")
            return False
        return True
    except RedisError as e:
        logger.error("Redis error during rate limit check", extra={"client_id": client_id, "error": str(e)})
        return True

def _domain_allowed(hostname: str) -> bool:
    # Placeholder for a domain allowlist/blocklist
    return True

def _validate_and_resolve_target(url: str) -> tuple[bool, str, str]:
    """
    Validate URL and return resolved IP address to use.
    Returns (is_valid, error_message, resolved_ip_to_use)

    This prevents DNS rebinding by resolving ONCE during validation,
    then using that exact IP for the request.
    """
    try:
        parsed = urlparse(url)
    except Exception:
        return False, "invalid url", None

    if parsed.scheme not in ("http", "https"):
        return False, "scheme not allowed", None

    hostname = parsed.hostname
    if not hostname:
        return False, "missing hostname", None

    # Block localhost explicitly (all forms)
    localhost_variations = {
        "localhost", "127.0.0.1", "::1",
        "0.0.0.0", "[::]", "0177.0.0.1",  # octal
        "0x7f.0.0.1", "127.1",             # hex, shortened
        "2130706433",                       # decimal
    }
    if hostname.lower() in localhost_variations:
        SSRF_BLOCKS.labels(reason='localhost_variation', hostname=hostname).inc()
        return False, "hostname not allowed", None

    # Domain allowlist check
    if not _domain_allowed(hostname):
        SSRF_BLOCKS.labels(reason='domain_not_allowed', hostname=hostname).inc()
        return False, "domain not allowed", None

    # Resolve ALL addresses (IPv4 + IPv6) and validate each
    try:
        addr_infos = socket.getaddrinfo(
            hostname,
            parsed.port or (443 if parsed.scheme == "https" else 80),
            socket.AF_UNSPEC,  # Both IPv4 and IPv6
            socket.SOCK_STREAM
        )
    except socket.gaierror as e:
        logger.warning("DNS resolution failed", extra={"hostname": hostname, "error": str(e)})
        return False, "dns resolution failed", None

    if not addr_infos:
        return False, "no addresses resolved", None

    validated_ips = []
    for family, socktype, proto, canonname, sockaddr in addr_infos:
        ip_addr = sockaddr[0]

        try:
            ip_obj = ipaddress.ip_address(ip_addr)

            # Check if IP is private/reserved/special
            if (ip_obj.is_private or
                ip_obj.is_loopback or
                ip_obj.is_reserved or
                ip_obj.is_link_local or
                ip_obj.is_multicast or
                ip_obj.is_unspecified):
                logger.warning(
                    "DNS resolved to private/reserved IP",
                    extra={"hostname": hostname, "ip": ip_addr}
                )
                SSRF_BLOCKS.labels(reason='private_ip', hostname=hostname).inc()
                return False, "resolved to private or reserved IP", None

            # Block cloud metadata IPs explicitly
            cloud_metadata_blocks = [
                ipaddress.ip_network("169.254.0.0/16"),      # AWS, Azure, GCP IPv4
                ipaddress.ip_network("fd00:ec2::/32"),       # AWS IPv6
                ipaddress.ip_network("fe80::/10"),           # Link-local IPv6
            ]

            for block in cloud_metadata_blocks:
                if ip_obj in block:
                    logger.warning(
                        "DNS resolved to cloud metadata IP",
                        extra={"hostname": hostname, "ip": ip_addr}
                    )
                    SSRF_BLOCKS.labels(reason='cloud_metadata_ip', hostname=hostname).inc()
                    return False, "resolved to cloud metadata IP", None

            validated_ips.append(ip_addr)

        except ValueError:
            logger.warning("Invalid IP format", extra={"ip": ip_addr})
            return False, "invalid ip format", None

    if not validated_ips:
        return False, "no valid IPs after filtering", None

    # Return first validated IP
    # We'll use this IP directly in the request
    return True, "ok", validated_ips[0]


def process_http_job(job_payload):
    """
    Process a single HTTP job payload and perform a validated, rate-limited outbound HTTP request.
    
    Parameters:
        job_payload (dict): Job data with expected keys:
            - "url" (str): Required. The target URL to request.
            - "client_id" (str, optional): Identifier used for rate limiting; falls back to the URL hostname if omitted.
            - "method" (str, optional): HTTP method to use (default "GET").
            - "headers" (dict, optional): Request headers; if missing, a Host header for the original hostname will be added.
            - "timeout" (number, optional): Request timeout in seconds (default 10.0, capped by MAX_TIMEOUT).
    
    Returns:
        dict: A dictionary containing the result.
        On success:
            - "status_code" (int): HTTP status code returned by the remote host.
            - "elapsed_ms" (int): Round-trip elapsed time in milliseconds.
            - "content_length" (int): Number of response bytes read (0 if empty).
        On error:
            - "error" (str): Short error identifier/message (e.g., "invalid payload", "missing url", "rate limit exceeded", "request not allowed: <reason>", "external requests disabled", "redirects not allowed", "response too large", "ssl verification failed", "request failed").
            - "status_code" (int, optional): Present when a redirect was blocked.
    """
    REQUESTS.inc()
    start = time.time()

    if not isinstance(job_payload, dict):
        return {"error": "invalid payload"}

    url = job_payload.get("url")
    if not url:
        return {"error": "missing url"}

    # Use a client_id from the job payload for rate limiting, or fall back to the URL's hostname.
    try:
        client_id = job_payload.get("client_id", urlparse(url).hostname)
        if not check_rate_limit(client_id):
            logger.warning("Rate limit exceeded", extra={"client_id": client_id})
            return {"error": "rate limit exceeded"}
    except Exception:
        return {"error": "invalid url for rate limiting"}

    # Validate and get resolved IP
    valid, why, resolved_ip = _validate_and_resolve_target(url)
    if not valid:
        logger.warning(
            "Rejected outbound request during validation",
            extra={"url": url, "reason": why}
        )
        return {"error": f"request not allowed: {why}"}

    if not ALLOW_EXTERNAL:
        logger.warning("External requests disabled", extra={"url": url})
        return {"error": "external requests disabled"}

    method = job_payload.get("method", "GET").upper()
    headers = job_payload.get("headers", {}) or {}
    timeout = min(float(job_payload.get("timeout", 10.0)), MAX_TIMEOUT)

    # Parse URL and reconstruct with validated IP
    parsed = urlparse(url)

    # Build URL using resolved IP instead of hostname
    # This prevents DNS rebinding!
    if ":" in resolved_ip:  # IPv6
        ip_for_url = f"[{resolved_ip}]"
    else:
        ip_for_url = resolved_ip

    port_part = f":{parsed.port}" if parsed.port else ""
    request_url = f"{parsed.scheme}://{ip_for_url}{port_part}{parsed.path}"
    if parsed.query:
        request_url += f"?{parsed.query}"

    # Set Host header to original hostname (for virtual hosting)
    if "Host" not in headers:
        headers["Host"] = parsed.hostname

    try:
        # CRITICAL: Disable redirects to prevent redirect-based SSRF
        resp = requests.request(
            method,
            request_url,  # Using resolved IP, not hostname!
            headers=headers,
            timeout=timeout,
            allow_redirects=False,  # CRITICAL FIX
            verify=True,            # Enforce TLS verification
            stream=True,
        )

        # Check for redirect attempts
        if resp.status_code in (301, 302, 303, 307, 308):
            logger.warning(
                "Request attempted redirect (blocked)",
                extra={
                    "url": url,
                    "status": resp.status_code,
                    "location": resp.headers.get("Location")
                }
            )
            return {
                "error": "redirects not allowed",
                "status_code": resp.status_code
            }

        content = b""
        for chunk in resp.iter_content(chunk_size=8192):
            content += chunk
            if len(content) > MAX_CONTENT_SIZE:
                logger.warning("Response exceeded size limit", extra={"url": url})
                return {"error": "response too large"}

        result = {
            "status_code": resp.status_code,
            "elapsed_ms": int(resp.elapsed.total_seconds() * 1000),
            "content_length": len(content) if content else 0,
        }
    except requests.exceptions.SSLError as e:
        logger.error("SSL verification failed", extra={"url": url, "error": str(e)})
        result = {"error": "ssl verification failed"}
    except Exception as e:
        logger.exception("Error performing outbound request", extra={"url": url, "error": str(e)})
        result = {"error": "request failed"}

    elapsed = time.time() - start
    PROCESS_TIME.observe(elapsed)
    return result

def main():
    """
    Start the Prometheus metrics server and run the RQ worker to process background jobs.
    
    Reads METRICS_PORT from the environment to bind the metrics server, logs startup information (including Redis URL and queue name), creates an RQ Worker listening on the configured queue, and runs it with scheduler support; this call blocks while the worker runs.
    """
    metrics_port = int(os.getenv("METRICS_PORT", "8001"))
    start_metrics_server(metrics_port)

    logger.info("Starting RQ worker", extra={"redis": REDIS_URL, "queue": QUEUE_NAME})

    listen = [QUEUE_NAME]

    worker = Worker(list(map(Queue, listen)), connection=redis_conn)
    # The worker expects job func path e.g. "agents.background.worker.process_http_job"
    worker.work(with_scheduler=True)

if __name__ == "__main__":
    main()
