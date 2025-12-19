import asyncio
from autogen import ConversableAgent, LLMConfig

class TalentAcceleratorAgent:
    """
    An agent specializing in developer skills assessment and matching them
    to relevant opportunities, such as upskilling for green energy.
    """

    def __init__(self, llm_config: LLMConfig):
        self.llm_config = llm_config
        self.agent = self._create_agent()

    def _create_agent(self):
        return ConversableAgent(
            name="talent_accelerator",
            llm_config=self.llm_config,
            system_message="You assess developer skills and match them to opportunities, focusing on upskilling for current market needs.",
        )

    async def initialize(self):
        """Initializes the agent's tools."""
        print("[Talent Accelerator] Initializing skill assessment modules...")
        await asyncio.sleep(1)  # Simulate loading
        self._register_tools()
        print(f"[Talent Accelerator] 2 tools registered")
        print("[Talent Accelerator] Ready to accelerate talent! 🚀")

    def _register_tools(self):
        self.agent.register_function(
            function_map={
                "assess_skills": self.assess_skills,
                "match_to_opportunities": self.match_to_opportunities,
            }
        )

    @staticmethod
    def assess_skills(skills_json: str) -> str:
        """Assesses a developer's skills based on a provided JSON."""
        return "Assessment complete: Mid-level full-stack developer with potential for solar tech."

    @staticmethod
    def match_to_opportunities(assessed_skills: str) -> str:
        """Matches assessed skills to relevant job or training opportunities."""
        return "Opportunity found: Solar installation upskilling program."
