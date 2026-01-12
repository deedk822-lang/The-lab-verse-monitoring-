#!/usr/bin/env python3
import asyncio, json, logging
from aiohttp import web

log = logging.getLogger("A2A")
routes = web.RouteTableDef()


@routes.post("/a2a")
async def negotiate(req):
    body = await req.json()
    log.info("Negotiate %s", body)
    return web.json_response({"consensus": "agree", "plan": body.get("payload", {})})


async def start():
    app = web.Application()
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "localhost", 3000)
    await site.start()
    log.info("A2A bridge on http://localhost:3000/a2a")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(start())
