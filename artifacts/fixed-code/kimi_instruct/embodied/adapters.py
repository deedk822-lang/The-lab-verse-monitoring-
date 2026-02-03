# --------------------  A2A  --------------------
import logging
from typing import Dict

import aiohttp


class A2AAdapter:
    def __init__(self, base_url: str = "https://localhost:3000/a2a"):
        self.url = base_url
        self.log = logging.getLogger("A2AAdapter")

    async def execute(self, step: Dict, dry_run: bool) -> Dict:
        # Validate input data
        if not isinstance(step, dict):
            raise ValueError("Input must be a dictionary")
        if not isinstance(dry_run, bool):
            raise ValueError("Dry-run must be a boolean")

        if dry_run:
            self.log.debug("A2A dry-run %s", step.get("action"))
            return {"status": "ok", "output": "sim-negotiate", "duration": 0.3}
        payload = {
            "agents": step["agents"],
            "action": step["action"],
            "payload": step.get("data"),
        }
        async with aiohttp.ClientSession() as s:
            try:
                async with s.post(self.url, json=payload) as r:
                    if r.status == 200:
                        return {"status": "ok", "output": await r.json(), "duration": 0.8}
                    else:
                        raise Exception(f"Unexpected status code: {r.status}")
            except aiohttp.ClientError as e:
                self.log.error("Failed to send A2A request", exc_info=True)
                return {"status": "error", "error": str(e)}