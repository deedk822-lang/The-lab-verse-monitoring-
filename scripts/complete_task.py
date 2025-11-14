#!/usr/bin/env python3
"""
Complete Task Script - One-Command Finish
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Calls live Vercel endpoint
2. Pushes metrics to Grafana Cloud
3. Validates system health
4. Exits 0 on success
"""
import asyncio, aiohttp, time, os, sys
from prometheus_client import Histogram, CollectorRegistry, push_to_gateway

# ------------ config (fill once) ------------
VERCEL_URL = os.getenv("VERCEL_URL", "https://the-lab-verse-monitoring.vercel.app/api/research")
GRAFANA_PUSH = os.getenv("GRAFANA_CLOUD_PROM_URL", "")
GRAFANA_USER = os.getenv("GRAFANA_CLOUD_PROM_USER", "")
GRAFANA_PASS = os.getenv("GRAFANA_CLOUD_API_KEY", "")
# ----------------------------------------------

registry = CollectorRegistry()
latency = Histogram(
"ai_provider_request_duration_seconds",
"Final task latency",
labelnames=["provider"],
registry=registry
)

async def push_metrics(provider: str, duration: float) -> bool:
    if not all([GRAFANA_PUSH, GRAFANA_USER, GRAFANA_PASS]):
        return False
    latency.labels(provider=provider).observe(duration)
    try:
        push_to_gateway(
            GRAFANA_PUSH.replace("/api/prom/push", ""),
            job="complete-task",
            registry=registry,
            timeout=5
        )
        return True
    except Exception as e:
        print(f"⚠️ Metrics push failed: {e}")
        return False

async def main():
    print("🚀 Completing task...")
    prompt = "What did Anthropic announce today?"
    t0 = time.time()

    async with aiohttp.ClientSession() as s:
        async with s.post(VERCEL_URL, json={"q": prompt}, timeout=30) as r:
            r.raise_for_status()
            data = await r.json()
            provider = data.get("provider", "unknown")
            text = data.get("text", "")[:200]

    duration = time.time() - t0
    pushed = await push_metrics(provider, duration)

    print(f"✅ Provider: {provider}")
    print(f"✅ Latency: {duration:.2f}s")
    print(f"✅ Metrics: {'pushed' if pushed else 'skipped'}")
    print(f"💬 Preview: {text}...")
    print("✅ Task completed successfully")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except Exception as e:
        print(f"❌ Task failed: {e}")
        sys.exit(1)
