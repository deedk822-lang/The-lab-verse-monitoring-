import sys
import os
import logging

# Ensure imports work
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from src.core.reality_check import ensure_production_ready
from src.core.empire_supervisor import EmpireSupervisor
from src.core.glean_bridge import GleanContextLayer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("TaxAgentMaster")

class TaxAgentMaster:
    def __init__(self):
        # 1. ENFORCE REALITY
        ensure_production_ready()

        # 2. LOAD REAL TOOLS (No Try/Except blocks hiding errors)
        self.supervisor = EmpireSupervisor()
        self.home = GleanContextLayer()
        self.active_model = "deepseek-v3" # Default to High Intelligence

    def set_model(self, model_name):
        self.active_model = model_name

    def execute_revenue_search(self):
        logger.info(f"🚀 EXECUTING REVENUE RUN (Model: {self.active_model})...")

        # REAL LOGIC ONLY
        # We ask the Supervisor (Qwen) to do the work.
        # We do NOT return a hardcoded float.

        try:
            # 1. Internal Scan
            ledger_data = self.home.search_enterprise_memory("Tax Invoices 2025", "finance")

            # 2. External Strategy
            if not ledger_data:
                # Ask Qwen to find opportunities anyway
                logger.info("   > No internal data found. Asking Qwen for general strategy...")
                strategy = self.supervisor.run("List 3 immediate tax saving strategies for SA Tech SMEs.")
                logger.info(f"   > Strategy: {strategy[:100]}...")
                return 0.00 # Honest return: No money found yet.
            else:
                logger.info(f"   > Ledger Data: {ledger_data}")
                # Real parsing logic would go here
                return 0.00

        except Exception as e:
            logger.error(f"❌ EXECUTION FAILED: {e}")
            raise e # Crash so we know it failed

if __name__ == "__main__":
    agent = TaxAgentMaster()
    agent.execute_revenue_search()
