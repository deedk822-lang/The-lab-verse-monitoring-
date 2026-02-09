# Numerai Agentic AI (Phase 1 + 2)

**Deployed in The Lab Verse Monitoring**

This module implements the **Perplexity Agentic Research API** pipeline for Numerai signal generation.

## Components

- **src/data/perplexity_devkit.py**: Core agentic fetcher using `client.responses.create`.
- **src/agents/numerai_crew.py**: Multi-agent system for analysis.
- **src/signals**: Signal generation logic.

## Usage

```bash
cd numerai-agentic-ai
pip install -r requirements.txt
python src/main.py
```

## Phase 2 Compliance
- Monitoring hooks enabled in `PerplexityNumeraiDevKit`.
- Structured logging.
- Error handling integration.
