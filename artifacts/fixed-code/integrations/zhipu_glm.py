async def generate_text(self, prompt: str, options: Optional[Dict] = None, sanitize: bool = True) -> str:
    """
    Generate text from the configured GLM model using the provided prompt.
    
    Parameters:
        prompt (str): The user prompt to send to the model.
        options (Optional[Dict]): Optional generation parameters. Supported keys:
                - "temperature" (float): Sampling temperature (default 0.7).
                - "max_tokens" (int): Requested max tokens; effective value is capped at 4096 (default 1024).
            sanitize (bool): If True, sanitize the prompt to mitigate prompt-injection risks before sending.
        
        Returns:
            str: The generated text content returned by the model.
        
        Raises:
            Exception: If the GLM API responds with a non-200 status or if an error occurs during the request.
    """
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
            # Sanitize the response to prevent potential security issues
            sanitized_response = self.sanitize_input(data["choices"][0]["message"]["content"])
            return sanitized_response

    except Exception as e:
        self.logger.error(f"Error generating text with GLM: {str(e)}")
        raise