import logging
import sys
import os

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

try:
    from src.core.empire_supervisor import EmpireSupervisor
except ImportError:
    EmpireSupervisor = None

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TaxAgentMaster")

class TaxAgentMaster:
    def __init__(self):
        self.supervisor = EmpireSupervisor() if EmpireSupervisor else None

    def execute_revenue_search(self):
        """
        The Daily Mission: Check for Tax Credits & Talent Revenue.
        """
        logger.info("--- TAX AGENT MASTER: STARTING RUN ---")

        if not self.supervisor:
            logger.error("❌ Supervisor Offline. Cannot execute.")
            raise RuntimeError("Dependency Missing: EmpireSupervisor")

        # 1. TAX MISSION (SARS)
        # We instruct the Supervisor (Qwen) to use the SARS tool
        logger.info("💰 Phase 1: SARS Tax Audit...")
        tax_result = self.supervisor.run(
            "Check for ETI claims on the payroll file 'oss://vaal-vault/payroll/latest.json' using sars_cash_flow_miner."
        )
        logger.info(f"   > Result: {tax_result}")

        # 2. TALENT MISSION (VanHack)
        # We instruct the Supervisor to check the resume queue
        logger.info("🌍 Phase 2: VanHack Talent Scan...")
        talent_result = self.supervisor.run(
            "Check the resume 'oss://vaal-vault/resumes/pending.pdf' for Canada eligibility using vanhack_crs_simulator."
        )
        logger.info(f"   > Result: {talent_result}")

        return True

if __name__ == "__main__":
    agent = TaxAgentMaster()
    try:
        agent.execute_revenue_search()
        sys.exit(0)
    except Exception as e:
        logger.error(f"FATAL: {e}")
        sys.exit(1)
