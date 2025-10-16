# --------------------  A2A  --------------------
import aiohttp, logging
from typing import Dict

class A2AAdapter:
    def __init__(self, base_url: str = "http://localhost:3000/a2a"):
        self.url = base_url
        self.log = logging.getLogger("A2AAdapter")

    async def execute(self, step: Dict, dry_run: bool) -> Dict:
        if dry_run:
            self.log.debug("A2A dry-run %s", step.get("action"))
            return {"status": "ok", "output": "sim-negotiate", "duration": 0.3}
        payload = {"agents": step["agents"], "action": step["action"], "payload": step.get("data")}
        async with aiohttp.ClientSession() as s:
            async with s.post(self.url, json=payload) as r:
                r.raise_for_status()
                return {"status": "ok", "output": await r.json(), "duration": 0.8}

# -------------------- WhatsApp & M-Pesa Stubs --------------------

class WhatsAppAdapter:
    def __init__(self):
        self.log = logging.getLogger("WhatsAppAdapter")

    async def send_message(self, user: str, text: str, dry_run: bool) -> Dict:
        self.log.info(f"Sending WhatsApp message to {user}: '{text}' (dry_run={dry_run})")
        return {"status": "ok", "message_id": "mock_whatsapp_id"}

class MPesaAdapter:
    def __init__(self):
        self.log = logging.getLogger("MPesaAdapter")

    async def make_payment(self, user: str, amount: float, dry_run: bool) -> Dict:
        self.log.info(f"Making M-Pesa payment of {amount} to {user} (dry_run={dry_run})")
        return {"status": "ok", "transaction_id": "mock_mpesa_id"}