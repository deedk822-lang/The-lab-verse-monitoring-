import asyncio
from aiohttp import web
from prometheus_client import start_http_server, Counter
from .metrics import OPTIMIZATION_RUNS_TOTAL, ANOMALIES_DETECTED_TOTAL
from .enhanced_optimizer import EnhancedCostOptimizer

async def handle_metrics(request):
    """
    Endpoint to serve Prometheus metrics.
    """
    # This is a simplified example. In a real application, you would
    # use the prometheus_client library to generate the metrics response.
    # For aiohttp, you might use a library like `aiohttp_prometheus`.
    # For now, we'll just return a placeholder.
    from prometheus_client.exposition import generate_latest
    return web.Response(body=generate_latest(), content_type="text/plain")


async def run_optimization(request):
    """
    A dummy endpoint to simulate running an optimization.
    """
    OPTIMIZATION_RUNS_TOTAL.labels(strategy="spot_instances", status="success").inc()
    return web.json_response({"status": "optimization run simulated"})


async def detect_anomalies(request):
    """
    An endpoint to detect anomalies in a given dataset.
    Expects a JSON payload with a "data" key.
    """
    try:
        payload = await request.json()
        data = payload.get("data")
        if data is None:
            return web.json_response({"error": "Missing 'data' in request body"}, status=400)

        optimizer = EnhancedCostOptimizer()
        anomalies = await optimizer.detect_anomalies(data)

        if anomalies:
            ANOMALIES_DETECTED_TOTAL.labels(anomaly_type="spike").inc(len(anomalies))

        return web.json_response({"anomalies": anomalies})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


def main():
    app = web.Application()
    app.router.add_get("/metrics", handle_metrics)
    app.router.add_post("/run_optimization", run_optimization)
    app.router.add_post("/detect_anomalies", detect_anomalies)

    # In a real app, you'd likely run the web server and background tasks
    # in a more sophisticated way.
    print("Starting cost optimizer service on port 8083...")
    web.run_app(app, port=8083)


if __name__ == "__main__":
    main()