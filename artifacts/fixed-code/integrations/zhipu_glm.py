# __aexit__ method with exception handling
async def __aexit__(self, exc_type, exc_val, exc_tb):
    try:
        await self.session.close()
    except Exception as e:
        self.logger.error(f"Error closing HTTP session: {e!s}")

# generate_text method with error handling
async def generate_text(self, prompt: str, options: dict[str, Any] | None = None, sanitize: bool = True) -> str:
    if options is None:
        options = {}

    # Sanitize the prompt to prevent injection if requested
    final_prompt = self.sanitize_input(prompt) if sanitize else prompt

    payload = {
        "model": self.config.model,
        "messages": [
            {"role": "user", "content": final_prompt}
        ],
        "temperature": options.get("temperature", 0.7),
        "max_tokens": min(options.get("max_tokens", 1024), 4096),
        "stream": False
    }

    try:
        async with self.session.post(
            self.config.base_url,
            json=payload
        ) as response:
            if response.status != 200:
                self.logger.error(f"GLM API returned status {response.status}: {await response.text()}")
                raise Exception(f"GLM API returned status {response.status}")

            data = await response.json()
            return data["choices"][0]["message"]["content"]

    except aiohttp.ClientError as e:
        self.logger.error(f"Error making HTTP request to GLM API: {e!s}")
        raise