"""
Backend Scheduler Service
Replaces Vercel Cron Jobs
"""
import asyncio
import logging
from datetime import datetime
import httpx
import os

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='{"time":"%(asctime)s", "level":"%(levelname)s", "message":"%(message)s"}'
)
logger = logging.getLogger(__name__)

API_URL = os.getenv("API_URL", "http://localhost:8080")

async def sync_integrations():
    """Sync all platform integrations"""
    logger.info("Syncing platform integrations...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{API_URL}/api/sync",
                json={"platforms": []},
                timeout=60.0
            )
            response.raise_for_status()
            logger.info(f"Sync completed: {response.status_code}")
        except Exception as e:
            logger.error(f"Sync failed: {e}")

async def health_check():
    """Health check"""
    logger.info("Running health check...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{API_URL}/health", timeout=5.0)
            if response.status_code == 200:
                logger.info("✓ API is healthy")
            else:
                logger.warning(f"✗ API returned {response.status_code}")
        except Exception as e:
            logger.error(f"Health check failed: {e}")


async def monitor_bandwidth():
    """Triggers the bandwidth monitoring task."""
    logger.info("Running bandwidth monitor...")
    async with httpx.AsyncClient() as client:
        try:
            # Vercel cron paths are typically GET requests unless data is sent
            response = await client.get(f"{API_URL}/api/bandwidth-monitor", timeout=30.0)
            response.raise_for_status()
            logger.info(f"Bandwidth monitor completed: {response.status_code}")
        except Exception as e:
            logger.error(f"Bandwidth monitor failed: {e}")


async def run_scheduler():
    """Main scheduler loop"""
    logger.info("Scheduler started")

    sync_interval = 300  # 5 minutes
    health_interval = 120  # 2 minutes
    bandwidth_interval = 21600  # 6 hours

    last_sync = 0
    last_health = 0
    last_bandwidth_check = 0

    while True:
        try:
            current_time = datetime.utcnow().timestamp()

            # Run sync every 5 minutes
            if current_time - last_sync >= sync_interval:
                await sync_integrations()
                last_sync = current_time

            # Run health check every 2 minutes
            if current_time - last_health >= health_interval:
                await health_check()
                last_health = current_time

            # Run bandwidth check every 6 hours
            if current_time - last_bandwidth_check >= bandwidth_interval:
                await monitor_bandwidth()
                last_bandwidth_check = current_time

            # Sleep for 30 seconds
            await asyncio.sleep(30)

        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(run_scheduler())
