import asyncio
from aiohttp import web
import json
from datetime import datetime, date
from enum import Enum
from .core import KimiInstruct, TaskPriority

def default_serializer(o):
    if isinstance(o, (datetime, date)):
        return o.isoformat()
    if isinstance(o, Enum):
        return o.value
    raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")

async def handle_status(request):
    """
    Handles requests for the Kimi Instruct status report.
    """
    kimi = request.app['kimi']
    report = await kimi.get_status_report()
    return web.json_response(report, dumps=lambda x: json.dumps(x, default=default_serializer))

async def handle_create_task(request):
    """
    Handles requests to create a new task.
    """
    try:
        kimi = request.app['kimi']
        data = await request.json()

        task = await kimi.create_task(
            title=data['title'],
            description=data.get('description', ''),
            priority=TaskPriority(data.get('priority', 'medium')),
            assigned_to=data.get('assigned_to', 'kimi'),
            human_approval_required=data.get('human_approval_required', False)
        )
        return web.json_response({'task_id': task.id}, status=201)
    except (KeyError, ValueError) as e:
        return web.json_response({'error': str(e)}, status=400)

async def handle_health(request):
    """
    A simple health check endpoint.
    """
    return web.json_response({"status": "healthy"})

def main():
    app = web.Application()
    app['kimi'] = KimiInstruct()

    app.router.add_get("/status", handle_status)
    app.router.add_post("/tasks", handle_create_task)
    app.router.add_get("/health", handle_health)

    print("Starting Kimi Instruct service on port 8084...")
    web.run_app(app, port=8084)

if __name__ == "__main__":
    from datetime import datetime, date
    from enum import Enum
    main()