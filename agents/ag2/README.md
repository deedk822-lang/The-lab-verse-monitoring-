# Vaal AI Empire - AG2 Multi-Agent System

🤖 **Overview**
This directory contains the AG2-powered multi-agent orchestration for the Vaal AI Empire. AG2 (formerly AutoGen) enables sophisticated collaboration between specialized AI agents.

🏗️ **Architecture**
```
User Request
     ↓
[Orchestrator]
     ↓
  ┌──────────────────────────┐
  │   AG2 AutoPattern        │
  │  (Automatic Routing)     │
  └──────────────────────────┘
     ↓         ↓         ↓
[Financial] [Guardian] [Talent]
[Sentinel]  [Engine]   [Accelerator]
     ↓         ↓         ↓
  SARS KB   Crisis    Skills
           Detector   Assessor
     ↓         ↓         ↓
  Cohere    Cohere    Cohere
  Search    Search    Search
```

🔥 **Agents**
**1. Financial Sentinel Agent**
*File: `financial_sentinel_agent.py`*

**Capabilities:**
- ✅ Query SARS regulations (semantic search)
- ✅ Calculate Section 12H learnership allowances
- ✅ Calculate ETI (Employment Tax Incentive)
- ✅ Cite official sources
- ✅ Provide tax-saving recommendations

**Tools:**
- `query_sars_regulations(query)` - Search SARS knowledge base
- `calculate_section_12h(learnerships_json)` - Calculate Section 12H recovery
- `calculate_eti(employees_json)` - Calculate ETI savings

**Example:**
```python
from agents.ag2.financial_sentinel_agent import FinancialSentinelAgent
from autogen import LLMConfig

llm_config = LLMConfig.from_json(path="OAI_CONFIG_LIST")
sentinel = FinancialSentinelAgent(llm_config)
await sentinel.initialize()

# Agent automatically uses tools when needed
response = sentinel.agent.run(
    recipient=sentinel.agent,
    message="Calculate tax recovery for 10 NQF level 5 learnerships",
    max_turns=5
)
```

**2. Guardian Engine Agent**
*File: `guardian_engine_agent.py`*

**Capabilities:**
- ✅ Assess load-shedding risk (color-coded alerts)
- ✅ Query crisis intelligence
- ✅ Get business impact by sector
- ✅ Provide proactive recommendations

**Tools:**
- `assess_loadshedding_risk(eaf, unplanned_outages_mw, coal_stockpile_days)` - Risk assessment
- `query_crisis_intelligence(query)` - Search crisis database
- `get_business_impact(sector, stage)` - Sector-specific impact

**Example:**
```python
from agents.ag2.guardian_engine_agent import GuardianEngineAgent

guardian = GuardianEngineAgent(llm_config)
await guardian.initialize()

response = guardian.agent.run(
    recipient=guardian.agent,
    message="What's the current load-shedding risk if EAF is 58%?",
    max_turns=3
)
```

**3. Orchestrator**
*File: `orchestrator.py`*

**Capabilities:**
- ✅ AutoPattern (automatic agent selection)
- ✅ Sequential workflows (Financial → Guardian → Human)
- ✅ Tax recovery + crisis analysis workflow
- ✅ Human-in-the-loop approvals

**Usage:**
```python
from agents.ag2.orchestrator import VaalAIEmpireOrchestrator

orchestrator = VaalAIEmpireOrchestrator()
await orchestrator.initialize()

# AutoPattern - AG2 picks best agent
result = await orchestrator.auto_pattern(
    task="Calculate my tax recovery and check for load-shedding risks",
    max_rounds=20,
    require_human_approval=True
)

# Specialized workflow
result = await orchestrator.tax_recovery_workflow({
    'learnerships': [...],
    'employees': [...],
    'sector': 'manufacturing',
    'current_eaf': 62.5
})
```

🚀 **Quick Start**
1. **Install Dependencies**
   ```bash
   pip install ag2[openai] cohere-ai hnswlib-node
   ```
2. **Configure API Keys**
   Create `OAI_CONFIG_LIST` in project root:
   ```json
   [
     {
       "model": "gpt-4o",
       "api_key": "sk-..."
     }
   ]
   ```
   Add to `.env`:
   ```
   COHERE_API_KEY=your_cohere_api_key
   ```
3. **Run Test**
   ```bash
   python agents/ag2/orchestrator.py
   ```
   Expected output:
   ```
   [Orchestrator] 🔥 Initializing Vaal AI Empire...
   [Financial Sentinel] Initializing SARS knowledge base...
   [Financial Sentinel] 3 tools registered
   [Financial Sentinel] Ready to recover tax money! 💰
   [Guardian Engine] Initializing crisis detection system...
   [Guardian Engine] 3 tools registered
   [Guardian Engine] Ready to protect businesses! 🛡️
   [Orchestrator] ✅ Vaal AI Empire ready!

   ==================================================
   Agent Status:
     financial_sentinel: ✅ Online
     guardian_engine: ✅ Online
     human_proxy: ✅ Ready
     orchestrator: ✅ Initialized
   ==================================================

   💰 Section 12H Tax Recovery
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Total Recovery: R60,000
   Tax Saving (28%): R16,800
   ...
   ```

🎯 **Workflows**
**AutoPattern Workflow**
```python
# AG2 automatically routes to best agent
result = await orchestrator.auto_pattern(
    task="I have 15 employees aged 22-28 earning R4500/month. "
         "Calculate my ETI and check if load-shedding will affect payroll processing.",
    max_rounds=15
)
```
**Flow:**
1. AG2 analyzes task
2. Routes to Financial Sentinel for ETI calculation
3. Routes to Guardian Engine for load-shedding check
4. Combines insights into final recommendation

**Sequential Workflow**
```python
result = await orchestrator.sequential_workflow(
    task="Calculate tax recovery for my company",
    workflow_steps=['financial_sentinel', 'guardian_engine', 'human']
)
```
**Flow:**
1. Financial Sentinel → Calculates tax recovery
2. Guardian Engine → Checks crisis risks
3. Human → Approves final recommendation

**Tax Recovery + Crisis Workflow**
```python
result = await orchestrator.tax_recovery_workflow({
    'learnerships': [
        {'nqf_level': 5, 'disabled': False, 'completed': True},
        {'nqf_level': 8, 'disabled': False, 'completed': True}
    ],
    'employees': [
        {'age': 24, 'monthly_salary': 4000, 'months_employed': 6}
    ],
    'sector': 'manufacturing',
    'current_eaf': 58.2
})
```
**Output:**
```json
{
  "tax_recovery": "Total Recovery: R60,000 | Tax Saving: R16,800",
  "crisis_assessment": "🔴 RED ALERT: EAF at 58% - Stage 4 loadshedding likely in 48h",
  "company_data": {...}
}
```

🛠️ **Tools Reference**
**Financial Sentinel Tools**

| Tool                      | Input                   | Output                                 |
| ------------------------- | ----------------------- | -------------------------------------- |
| `query_sars_regulations`  | `query: str`            | SARS regulations with relevance scores |
| `calculate_section_12h`   | `learnerships_json: str`| Total recovery + tax savings           |
| `calculate_eti`           | `employees_json: str`   | Monthly ETI + annual ETI               |

**Guardian Engine Tools**

| Tool                          | Input                                                     | Output                                              |
| ----------------------------- | --------------------------------------------------------- | --------------------------------------------------- |
| `assess_loadshedding_risk`    | `eaf: float`, `unplanned_outages_mw: int`, `coal_stockpile_days: int` | Color-coded risk alert + recommendations        |
| `query_crisis_intelligence`   | `query: str`                                              | Crisis intelligence with relevance scores         |
| `get_business_impact`         | `sector: str`, `stage: int`                               | Business impact + mitigation strategies           |

🔐 **Human-in-the-Loop**
**When to use:**
- Payment approvals (>R10,000)
- SARS submission confirmations
- Contract signing
- Compliance decisions

**Example:**
```python
result = await orchestrator.auto_pattern(
    task="Submit R50,000 tax claim to SARS",
    require_human_approval=True  # ← Human must approve
)
```
**Flow:**
1. Financial Sentinel calculates R50,000 recovery
2. Human Proxy Agent prompts: "APPROVED or REJECT?"
3. User types: `APPROVED`
4. Guardian Engine monitors SARS response time

📊 **Performance**
- **Initialization time:** ~10-15 seconds (embeddings generation)
- **Query latency:** 2-5 seconds (Cohere semantic search + rerank)
- **Tool execution:** <1 second (local calculations)
- **AG2 routing:** <500ms (LLM decides which agent)

🧪 **Testing**
```bash
# Test individual agents
python -c "
import asyncio
from agents.ag2.financial_sentinel_agent import FinancialSentinelAgent
from autogen import LLMConfig

async def test():
    llm = LLMConfig.from_json('OAI_CONFIG_LIST')
    agent = FinancialSentinelAgent(llm)
    await agent.initialize()
    print('✅ Financial Sentinel OK')

asyncio.run(test())
"

# Test orchestrator
python agents/ag2/orchestrator.py
```

🎯 **Next Steps**
- Add Talent Accelerator Agent - Skills assessment + job matching
- Express API Integration - Expose agents via REST endpoints
- Caching Layer - Redis for repeated queries
- Monitoring - Track agent performance, costs, errors
- A/B Testing - Compare AG2 vs. manual orchestration

---
*Built in the Vaal Triangle. Powered by AG2. Verified by SARS.*

© 2025 Vaal AI Empire
