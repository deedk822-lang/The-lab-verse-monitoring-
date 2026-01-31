# --------------------  A2A  --------------------
import logging
from typing import Dict

import aiohttp


class A2AAdapter:
    def __init__(self, base_url: str = "http://localhost:3000/a2a"):
        self.url = base_url
        self.log = logging.getLogger("A2AAdapter")

    async def execute(self, step: Dict, dry_run: bool) -> Dict:
        if dry_run:
            self.log.debug("A2A dry-run %s", step.get("action"))
            return {"status": "ok", "output": "sim-negotiate", "duration": 0.3}
        payload = {
            "agents": step["agents"],
            "action": step["action"],
            "payload": step.get("data"),
        }
        async with aiohttp.ClientSession() as s:
            async with s.post(self.url, json=payload) as r:
                r.raise_for_status()
                return {"status": "ok", "output": await r.json(), "duration": 0.8}
