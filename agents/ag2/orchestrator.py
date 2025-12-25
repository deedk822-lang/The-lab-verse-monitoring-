import asyncio
from autogen import ConversableAgent, LLMConfig
from autogen.agentchat.group.patterns import AutoPattern
from dotenv import load_dotenv

from agents.ag2.financial_sentinel_agent import FinancialSentinelAgent
from agents.ag2.guardian_engine_agent import GuardianEngineAgent
from agents.ag2.talent_accelerator_agent import TalentAcceleratorAgent
from agents.ag2.sars_monitor_agent import SARSMonitorAgent

load_dotenv()

class VaalAIEmpireOrchestrator:
    def __init__(self):
        self.llm_config = self._load_llm_config()
        self.financial_sentinel = FinancialSentinelAgent(self.llm_config)
        self.guardian_engine = GuardianEngineAgent(self.llm_config)
        self.talent_accelerator = TalentAcceleratorAgent(self.llm_config)
        self.sars_monitor = SARSMonitorAgent(self.llm_config)

    def _load_llm_config(self):
        try:
            return LLMConfig.from_json(env_or_file="OAI_CONFIG_LIST")
        except ValueError:
            print("Could not find OAI_CONFIG_LIST file. Using dummy config.")
            return LLMConfig(config_list=[{"model": "gpt-4", "api_key": "dummy"}])

    async def initialize(self):
        print("[Orchestrator] 🔥 Initializing Vaal AI Empire...")
        await self.financial_sentinel.initialize()
        await self.guardian_engine.initialize()
        await self.talent_accelerator.initialize()
        await self.sars_monitor.initialize()
        print("[Orchestrator] ✅ Vaal AI Empire ready!")

    def get_auto_pattern(self):
        return AutoPattern(
            agents=[
                self.financial_sentinel.agent,
                self.guardian_engine.agent,
                self.talent_accelerator.agent,
                self.sars_monitor.agent,
            ],
            initial_agent=self.financial_sentinel.agent,
            group_manager_args={"name": "empire_manager", "llm_config": self.llm_config}
        )

async def main():
    orchestrator = VaalAIEmpireOrchestrator()
    await orchestrator.initialize()

    print("\n🚀 AutoPattern Orchestration Initialized")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    # This will create the pattern but not run it in this example
    empire_pattern = orchestrator.get_auto_pattern()
    print(f"Initialized AutoPattern with initial agent: {empire_pattern.initial_agent.name}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\nCould not run orchestrator main function: {e}")
        print("This is expected if you have not set up your OAI_CONFIG_LIST file.")
