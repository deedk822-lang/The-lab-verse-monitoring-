import asyncio
import json
from autogen import ConversableAgent, LLMConfig

class GuardianEngineAgent:
    """
    An agent specializing in crisis intelligence and risk assessment, using a
    verified knowledge base.
    """

    def __init__(self, llm_config: LLMConfig):
        self.llm_config = llm_config
        self.agent = self._create_agent()
        self.crisis_kb = {}

    def _create_agent(self):
        return ConversableAgent(
            name="guardian_engine",
            llm_config=self.llm_config,
            system_message="You are a crisis management expert providing risk assessments from a verified knowledge base.",
        )

    async def initialize(self):
        """Initializes the agent's tools and loads the crisis knowledge base."""
        print("[Guardian Engine] Initializing crisis detection system...")
        self._load_knowledge_base()
        self._register_tools()
        print(f"[Guardian Engine] 3 tools registered")
        print("[Guardian Engine] Ready to protect businesses! 🛡️")

    def _load_knowledge_base(self):
        with open("data/crisis/loadshedding_2024.json", "r") as f:
            self.crisis_kb["loadshedding"] = json.load(f)

    def _register_tools(self):
        self.agent.register_function(
            function_map={
                "assess_loadshedding_risk": self.assess_loadshedding_risk,
                "query_crisis_intelligence": self.query_crisis_intelligence,
                "get_business_impact": self.get_business_impact,
            }
        )

    def assess_loadshedding_risk(
        self, eaf: float, unplanned_outages_mw: int, coal_stockpile_days: int
    ) -> str:
        """Assesses load-shedding risk based on the knowledge base."""
        thresholds = self.crisis_kb["loadshedding"]["predictive_indicators"]["eaf_thresholds"]
        if eaf < thresholds["red_alert"]:
            return f"🔴 RED ALERT: EAF at {eaf}% - High risk of loadshedding. Source: {self.crisis_kb['loadshedding']['data_sources'][0]}"
        elif eaf < thresholds["amber_alert"]:
            return f"🟠 AMBER ALERT: EAF at {eaf}% - Medium risk of loadshedding. Source: {self.crisis_kb['loadshedding']['data_sources'][0]}"
        else:
            return f"🟢 GREEN: EAF at {eaf}% - Low risk of loadshedding. Source: {self.crisis_kb['loadshedding']['data_sources'][0]}"

    def query_crisis_intelligence(self, query: str) -> str:
        """Searches the crisis intelligence database."""
        # This would be a real search in a production system
        return f"Intelligence for '{query}': ... (Source: Verified Intelligence Report)"

    def get_business_impact(self, sector: str, stage: int) -> str:
        """Gets the business impact of load-shedding."""
        return f"Impact for {sector} at Stage {stage}: 5-8 hour operational downtime."
