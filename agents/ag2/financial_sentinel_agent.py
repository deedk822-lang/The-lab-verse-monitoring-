import asyncio
import json
import os
from autogen import ConversableAgent, LLMConfig

class FinancialSentinelAgent:
    """
    An agent specializing in South African tax regulations, using a verified
    knowledge base for calculations.
    """

    def __init__(self, llm_config: LLMConfig):
        self.llm_config = llm_config
        self.agent = self._create_agent()
        self.sars_kb = {}

    def _create_agent(self):
        return ConversableAgent(
            name="financial_sentinel",
            llm_config=self.llm_config,
            system_message="You are a financial expert specializing in SARS tax incentives, using a verified knowledge base.",
        )

    async def initialize(self):
        """Initializes the agent's tools and loads the SARS knowledge base."""
        print("[Financial Sentinel] Initializing SARS knowledge base...")
        self._load_knowledge_base()
        self._register_tools()
        print(f"[Financial Sentinel] 3 tools registered")
        print("[Financial Sentinel] Ready to recover tax money! 💰")

    def _load_knowledge_base(self):
        # Construct path relative to this script's location
        script_dir = os.path.dirname(__file__)
        project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))

        section_12h_path = os.path.join(project_root, "data", "sars", "section_12h_learnerships.json")
        with open(section_12h_path, "r") as f:
            self.sars_kb["section_12h"] = json.load(f)

        eti_path = os.path.join(project_root, "data", "sars", "eti_employment_incentive.json")
        with open(eti_path, "r") as f:
            self.sars_kb["eti"] = json.load(f)

    def _register_tools(self):
        self.agent.register_function(
            function_map={
                "query_sars_regulations": self.query_sars_regulations,
                "calculate_section_12h": self.calculate_section_12h,
                "calculate_eti": self.calculate_eti,
            }
        )

    def query_sars_regulations(self, query: str) -> str:
        """Searches the SARS knowledge base for tax regulations."""
        # This would be a real search in a production system
        return f"Results for '{query}': Based on {self.sars_kb['section_12h']['official_sources'][0]}, ..."

    def calculate_section_12h(self, learnerships_json: str) -> str:
        """Calculates Section 12H learnership allowances from the knowledge base."""
        # Simplified calculation for demonstration
        allowance = self.sars_kb["section_12h"]["allowances"]["annual_allowance"]["nqf_1_to_6"]["able_bodied"]
        return f"Total Recovery: R{allowance} per learnership | Source: {self.sars_kb['section_12h']['official_sources'][0]}"

    def calculate_eti(self, employees_json: str) -> str:
        """Calculates Employment Tax Incentive (ETI) from the knowledge base."""
        allowance = self.sars_kb["eti"]["monthly_allowances"]["first_12_months"]["0-2000"]
        return f"Monthly ETI: R{allowance} per qualifying employee | Source: {self.sars_kb['eti']['sources'][0]}"
