# Vaal AI Empire

This repository contains the Vaal AI Empire project, including the Tax Agent Humanitarian Revenue Engine.

## Tax Agent Humanitarian Revenue Engine

The Tax Agent is a single, unified workflow that demonstrates a complete, end-to-end process from data fetching to content creation and event logging.

### Single, Real Execution Command

To run the entire, real workflow from start to finish, use the following command. This command will install all necessary dependencies and then execute the main workflow script.

**Note:** You must have your API keys for NewsAPI.ai, Perplexity, Cohere, and Groq set as environment variables for this command to work.

```bash
pip install -r vaal-ai-empire/requirements.txt && \
NEWSAPI_AI_API_KEY=$NEWSAPI_AI_API_KEY \
PPLX_API_KEY=$PPLX_API_KEY \
COHERE_API_KEY=$COHERE_API_KEY \
GROQ_API_KEY=$GROQ_API_KEY \
python3 vaal-ai-empire/scripts/run_tax_agent_workflow.py
```
