import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class KimiIndustryAgent:
    """
    An agent that uses the Kimi K2 model to organize industry information.
    """
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("KIMI_API_KEY"),
            base_url="https://api.moonshot.ai/v1",
        )

    def run(self, query: str) -> str:
        """
        Runs the agent with the given query.

        Args:
            query: The query to send to the agent.

        Returns:
            The agent's response.
        """
        completion = self.client.chat.completions.create(
            model="kimi-k2-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are Kimi, an AI assistant provided by Moonshot AI. You are proficient in Chinese and English conversations. You provide users with safe, helpful, and accurate answers. You will reject any questions involving terrorism, racism, or explicit content. Moonshot AI is a proper noun and should not be translated.",
                },
                {"role": "user", "content": query},
            ],
            temperature=0.6,
            tools=[
                {"type": "web_search"},
                {"type": "code_runner"},
                {"type": "rethink"},
            ],
        )
        return completion.choices[0].message.content
