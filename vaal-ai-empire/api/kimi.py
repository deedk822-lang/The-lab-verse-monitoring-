import os
from openai import OpenAI

class KimiClient:
    def __init__(self):
        api_key = os.getenv("KIMI_API_KEY")
        if not api_key:
            raise ValueError("KIMI_API_KEY environment variable not set. Please check your .env file or environment settings.")
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.moonshot.ai/v1",
        )

    def generate(self, prompt: str) -> str:
        """
        Generates a response from the Kimi/Moonshot AI model.
        """
        try:
            completion = self.client.chat.completions.create(
                model="moonshot-v1-8k",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"An error occurred: {e}"

# Example usage:
if __name__ == "__main__":
    # Note: Requires KIMI_API_KEY to be set in the environment or a .env file
    # from dotenv import load_dotenv
    # load_dotenv()

    client = KimiClient()
    prompt = "Hello, who are you?"
    response = client.generate(prompt)
    print(response)
