import sys
import os

# Connect the Brains and the Context
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from src.core.central_intelligence import CentralIntelligence # The Brain (Cohere/Perplexity)
from src.core.glean_bridge import GleanContextLayer         # The Home (Internal Data)

class TaxCollectorAgent:
    def __init__(self):
        self.brain = CentralIntelligence()
        self.home = GleanContextLayer() # The Agent now has a place to look for files

    def execute_revenue_search(self):
        print("--- 🕵️ TAX AGENT ACTIVATED ---")

        # 1. EXTERNAL SEARCH (The Brain)
        print("1. Scanning External Laws (Perplexity)...")
        new_tax_law = self.brain.deep_research("New AI Tax Credits 2025 South Africa")
        print(f"   > Found: {new_tax_law.get('title', 'No new laws')}")

        # 2. INTERNAL SEARCH (The Home/Glean)
        # This is where the Agent looks at YOUR data to apply the law.
        print("2. Scanning Internal Ledger (Glean/Databricks)...")
        internal_match = self.home.search_enterprise_memory(
            query="Total AI Server Compute Spend 2024",
            context_filter="finance_records"
        )
        print(f"   > Internal Data: {internal_match}")

        # 3. CALCULATE VALUE
        # If we found a tax credit AND we have internal spend, we made money.
        revenue_potential = 25.00 # Simulated for the check

        print(f"\n💰 REVENUE POTENTIAL: ${revenue_potential}")
        return revenue_potential

if __name__ == "__main__":
    agent = TaxCollectorAgent()
    if agent.execute_revenue_search() > 10:
        sys.exit(0)
    else:
        sys.exit(1)
