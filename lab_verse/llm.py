import aiohttp, os, logging
from tenacity import retry, wait_exponential, stop_after_attempt

logger = logging.getLogger("llm")

GROK_URL = "https://api.x.ai/v1/chat/completions"
GROK_KEY = os.getenv("GROK_API_KEY")

@retry(wait=wait_exponential(multiplier=1, min=4, max=60), stop=stop_after_attempt(6))
async def call_grok_async(prompt: str, **kwargs) -> str:
    headers = {"Authorization": f"Bearer {GROK_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "grok-beta",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": kwargs.get("temperature", 0.7),
        "max_tokens": kwargs.get("max_tokens", 512),
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(GROK_URL, headers=headers, json=payload) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return data["choices"][0]["message"]["content"]