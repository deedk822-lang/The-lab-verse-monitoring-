import logging
from typing import Dict

import aiohttp


class A2AAdapter:
    def __init__(self, base_url: str = "http://localhost:3000/a2a"):
        self.url = base_url
        self.log = logging.getLogger(__name__)  # Use the class name for better logging

    async def execute(self, step: Dict, dry_run: bool) -> Dict:
        if dry_run:
            self.log.debug("A2A dry-run %s", step.get("action"))
            return {"status": "ok", "output": "sim-negotiate", "duration": 0.3}
        
        # Validate and sanitize the input
        try:
            validated_step = {
                "agents": step["agents"],
                "action": step["action"],
                "payload": step.get("data"),
            }
        except KeyError as e:
            self.log.error(f"Invalid key in step dictionary: {e}")
            return {"status": "error", "message": f"Missing required field: {str(e)}"}

        payload = {
            "agents": validated_step["agents"],
            "action": validated_step["action"],
            "payload": validated_step.get("payload"),
        }

        async with aiohttp.ClientSession() as s:
            async with s.post(self.url, json=payload) as r:
                try:
                    response = await r.json()
                except ValueError as e:
                    self.log.error(f"Failed to parse JSON response: {e}")
                    return {"status": "error", "message": str(e)}

                duration = r.elapsed.total_seconds()

                if r.status == 200:
                    return {
                        "status": "ok",
                        "output": response,
                        "duration": duration,
                    }
                else:
                    self.log.error(f"HTTP request failed with status code: {r.status}")
                    return {"status": "error", "message": f"Failed to complete negotiation. Status code: {r.status}"}