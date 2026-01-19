
import sys
from src.agents.tax_collector import TaxAgentMaster

print('🚀 ACTIVATING GUARDIAN (TITAN MODE)...')
agent = TaxAgentMaster()
# Force DeepSeek/Qwen Reasoning
agent.set_model('deepseek-v3')

# Execute Real Revenue Search (VanHack/Crisis)
revenue = agent.execute_revenue_search()
print(f'💰 GUARDIAN REPORT: Revenue Generated: R{revenue}')
