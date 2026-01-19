
from src.agents.tax_collector import TaxAgentMaster

print('📉 ACTIVATING TAX COMPLIANCE SCAN...')
agent = TaxAgentMaster()
# Use Standard Mode (Glean/Internal Data)
agent.set_model('standard')

# Execute Real Audit
result = agent.execute_revenue_search()
print(f'✅ COMPLIANCE CHECK COMPLETE. Value: R{result}')
