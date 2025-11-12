import os
import sys
import time
import aiohttp
import asyncio
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

async def main():
    # Get query from command-line arguments
    if len(sys.argv) < 2:
        print("Usage: python3 live_test_agent.py \"<query>\"")
        sys.exit(1)
    query = sys.argv[1]

    # Get environment variables
    vercel_url = os.getenv("VERCEL_URL")
    grafana_url = os.getenv("GRAFANA_CLOUD_PROM_URL")
    grafana_user = os.getenv("GRAFANA_CLOUD_PROM_USER")
    grafana_api_key = os.getenv("GRAFANA_CLOUD_API_KEY")

    if not all([vercel_url, grafana_url, grafana_user, grafana_api_key]):
        print("Error: Missing one or more required environment variables.")
        sys.exit(1)

    # Prepare Prometheus metrics
    registry = CollectorRegistry()
    g = Gauge('ai_agent_response_time_seconds', 'Response time of the AI agent', registry=registry)

    start_time = time.time()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(vercel_url, json={'q': query}) as response:
                response.raise_for_status()
                response_text = await response.text()
                print(f"Response from agent: {response_text}")
    except aiohttp.ClientError as e:
        print(f"Error calling Vercel endpoint: {e}")
        # In case of an error, we might want to push a specific value (e.g., -1)
        # For simplicity, we'll just exit here.
        sys.exit(1)
    finally:
        end_time = time.time()
        response_time = end_time - start_time
        g.set(response_time)

        try:
            push_to_gateway(
                grafana_url,
                job='ai_agent_test',
                registry=registry,
                handler=lambda url, method, timeout, headers, data: aiohttp.request(
                    method, url, timeout=timeout, headers=headers, data=data,
                    auth=aiohttp.BasicAuth(grafana_user, grafana_api_key)
                )
            )
            print(f"Successfully pushed metric to Grafana Cloud. Response time: {response_time:.2f}s")
        except Exception as e:
            print(f"Error pushing metric to Grafana Cloud: {e}")

if __name__ == "__main__":
    asyncio.run(main())
