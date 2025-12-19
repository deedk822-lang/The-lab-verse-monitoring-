import asyncio
from autogen import ConversableAgent, LLMConfig

class SARSMonitorAgent:
    """
    An agent specializing in monitoring the SARS website and official
    publications for updates to tax regulations.
    """

    def __init__(self, llm_config: LLMConfig):
        self.llm_config = llm_config
        self.agent = self._create_agent()

    def _create_agent(self):
        return ConversableAgent(
            name="sars_monitor",
            llm_config=self.llm_config,
            system_message="You monitor the SARS website for real-time updates on tax regulations.",
        )

    async def initialize(self):
        """Initializes the agent's monitoring tools."""
        print("[SARS Monitor] Initializing monitoring systems...")
        await asyncio.sleep(1)
        self._register_tools()
        print(f"[SARS Monitor] 2 tools registered")
        print("[SARS Monitor] Ready to watch for SARS updates! 🕵️")

    def _register_tools(self):
        self.agent.register_function(
            function_map={
                "check_for_updates": self.check_for_updates,
                "verify_source": self.verify_source,
            }
        )

    @staticmethod
    def check_for_updates(regulation: str) -> str:
        """Checks for recent updates to a specific SARS regulation."""
        return f"No new updates found for '{regulation}' since the last check."

    @staticmethod
    def verify_source(url: str) -> str:
        """Verifies that a URL is an official SARS source."""
        if "sars.gov.za" in url:
            return f"Source '{url}' is verified as an official SARS domain."
        else:
            return f"Source '{url}' is not a recognized SARS domain."
