import asyncio
import os
from autogen import ConversableAgent, UserProxyAgent, LLMConfig
from dotenv import load_dotenv

from agents.ag2.financial_sentinel_agent import FinancialSentinelAgent
from agents.ag2.guardian_engine_agent import GuardianEngineAgent

load_dotenv()

class VaalAIEmpireOrchestrator:
    """
    Orchestrates the AG2 multi-agent system for the Vaal AI Empire.
    """

    def __init__(self):
        self.llm_config = self._load_llm_config()
        self.financial_sentinel = FinancialSentinelAgent(self.llm_config)
        self.guardian_engine = GuardianEngineAgent(self.llm_config)
        self.human_proxy = self._create_human_proxy()

    def _load_llm_config(self):
        """Loads LLM config from OAI_CONFIG_LIST file."""
        try:
            return LLMConfig.from_json(
                env_or_file="OAI_CONFIG_LIST",
                file_location=".",
            )
        except ValueError:
            print("Could not find OAI_CONFIG_LIST file. Please configure it.")
            # Provide a dummy config to allow the script to be imported
            return LLMConfig(config_list=[{"model": "gpt-4", "api_key": "dummy"}])


    def _create_human_proxy(self):
        return UserProxyAgent(
            name="human_proxy",
            human_input_mode="NEVER", # Set to NEVER for non-interactive example
            code_execution_config=False,
        )

    async def initialize(self):
        """Initializes all agents in the system."""
        print("[Orchestrator] 🔥 Initializing Vaal AI Empire...")
        await self.financial_sentinel.initialize()
        await self.guardian_engine.initialize()
        print("[Orchestrator] ✅ Vaal AI Empire ready!")
        self.print_status()

    def print_status(self):
        print("\n==================================================")
        print("Agent Status:")
        print(f"  financial_sentinel: ✅ Online")
        print(f"  guardian_engine: ✅ Online")
        print(f"  human_proxy: ✅ Ready")
        print(f"  orchestrator: ✅ Initialized")
        print("==================================================")

    async def auto_pattern(self, task: str, max_rounds: int = 10, require_human_approval: bool = False):
        """Uses AG2's AutoPattern to automatically route the task to the best agent."""
        agents = [
            self.financial_sentinel.agent,
            self.guardian_engine.agent,
        ]
        if require_human_approval:
            self.human_proxy.human_input_mode = "ALWAYS"
            agents.append(self.human_proxy)
        else:
            self.human_proxy.human_input_mode = "NEVER"

        # This is a simplified setup for demonstration.
        # A real implementation would use a GroupChatManager.
        user_proxy = UserProxyAgent(
            name="user_proxy",
            human_input_mode="NEVER",
            code_execution_config=False,
            llm_config=self.llm_config,
            system_message="You are a proxy for the user.",
            is_termination_msg=lambda x: "FINAL ANSWER" in x.get("content", "").upper(),
        )

        for agent in agents:
            user_proxy.register_for_execution()(agent)
            agent.register_for_llm(user_proxy)

        await user_proxy.initiate_chat(self.financial_sentinel.agent, message=task)


async def main():
    """Main function to run a test of the orchestrator."""
    orchestrator = VaalAIEmpireOrchestrator()
    await orchestrator.initialize()

    print("\n🚀 Running AutoPattern Workflow Example")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    task = (
        "I have 15 employees aged 22-28 earning R4500/month. "
        "Calculate my ETI and check if load-shedding will affect payroll processing."
    )
    # This will use the dummy key and likely fail at the LLM call,
    # but it demonstrates the workflow setup.
    await orchestrator.auto_pattern(task)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\nCould not run orchestrator main function: {e}")
        print("This is expected if you have not set up your OAI_CONFIG_LIST file.")
