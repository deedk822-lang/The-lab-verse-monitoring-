import os
from qwen_agent.agents import Assistant
from src.core.revenue_attribution import AttributionEngine

class EmpireSupervisor:
    def __init__(self):
        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        self.finance = AttributionEngine()

        # Qwen-Max with Financial Awareness
        self.bot = Assistant(
            llm={'model': 'qwen-max'},
            name='Vaal CEO',
            system_message="You are the CEO. Check ROAS before approving marketing budgets."
        )

    def run_financial_audit(self):
        print("🕵️ QWEN: Running Weekly Financial Audit...")

        # 1. Get Hard Data
        metrics = self.finance.calculate_roas()

        # 2. Analyze Strategy
        prompt = f"""
        FINANCIAL REPORT:
        Spend: ${metrics['spend']}
        Revenue: ${metrics['revenue']}
        ROAS: {metrics['roas']}x

        TASK:
        Write a strategic directive.
        If ROAS > 3.0, suggest scaling ad spend.
        If ROAS < 3.0, suggest cutting costs.
        """

        response = self.bot.run(messages=[{'role': 'user', 'content': prompt}])

        report = ""
        for chunk in response:
            report += chunk.get('content', '')

        return report

if __name__ == "__main__":
    sup = EmpireSupervisor()
    print(sup.run_financial_audit())
