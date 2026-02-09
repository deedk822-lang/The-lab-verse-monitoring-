import os
import sys

# Add the 'vaal-ai-empire' directory to the Python path using a robust, __file__-relative path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'vaal-ai-empire'))

try:
    from src.core.empire_supervisor import EmpireSupervisor

    print("   > Initializing Qwen-Max...")
    supervisor = EmpireSupervisor()

    print("   > Running Diagnostics...")
    # We ask the Supervisor to check its own tools
    response = supervisor.run("System Check: Verify connection to VanHack Simulator and SARS Tax Miner.")

    print(f"\n🤖 SUPERVISOR RESPONSE:\n{response}\n")
    print("✅ EMPIRE IS AWAKE.")

except Exception as e:
    print(f"❌ WAKE UP FAILED: {e}")
    sys.exit(1)
