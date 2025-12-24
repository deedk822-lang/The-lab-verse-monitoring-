# 🚀 Rainmaker AI - The Multi-Model "Brain" Architecture

This repository contains the complete infrastructure for a production-grade, multi-model AI orchestration layer. It is a "mission control center" for your AI operations, designed for high performance, resilience, and intelligent task routing.

---

## ✨ Core Components

1.  **Multi-Model Serving (`docker-compose.superstack.yml`)**:
    *   **Kimi-Linear (vLLM)**: A sovereign, 1M context window model for large-scale data ingestion and processing, served with vLLM for maximum throughput.
    *   **Ollama**: A multi-model workbench for running a variety of specialized models (e.g., for reasoning, speed, or cost optimization).
    *   **Open WebUI**: A unified control panel for interacting with all models in the AI-circuit.

2.  **Rainmaker Orchestrator (`rainmaker-orchestrator/`)**:
    *   The "brain" of the system, this Python service intelligently routes tasks to the best model based on context size, task type, and cost.
    *   It includes an `AdaptiveModelRouter` for self-healing, which automatically falls back to the Kimi-Linear sovereign engine if a specialized model fails.

3.  **Monitoring (`prometheus.yml`, `grafana-dashboards/`)**:
    *   A full monitoring stack with Prometheus for metrics collection and Grafana for visualization.
    *   Track cost per task, model utilization, context size distribution, and more.

---

## 🚀 Quick Start

### 1. Prerequisites
- Docker and Docker Compose
- NVIDIA GPU with CUDA drivers installed
- An environment with the `HF_TOKEN` environment variable set to your Hugging Face Hub token.

### 2. Launch the Superstack

This single command will build and launch the entire multi-model ecosystem.

```bash
# One-command stack deployment
docker compose -f docker-compose.superstack.yml up -d --build
```

### 3. Monitor the Brain

```bash
# Watch the brain come online
docker logs -f rainmaker-orchestrator

# Access control panels
- **Open WebUI**: http://localhost:3000
- **Grafana (brain visualizer)**: http://localhost:3001 (Password: `r41nm4k3r`)
- **Prometheus**: http://localhost:9090
```

### 4. Use the Orchestrator CLI

The `rainmaker_cli.py` script is the primary tool for interacting with the orchestrator.

```bash
# Example 1: Debug a Python script
python scripts/rainmaker_cli.py code_debugging ./path/to/your/script.py

# Example 2: Ingest a large text file
python scripts/rainmaker_cli.py ingestion ./path/to/large_document.txt

# Example 3: Get a strategy for a business problem
python scripts/rainmaker_cli.py strategy "What are the key risks for a new SaaS business?"
```

---

## 🏛️ The Thabo Mbeki Presidential Library Digital Archive

This project also includes the foundational components for the Thabo Mbeki Presidential Library's digital archive, a major new initiative focused on cultural reclamation and the preservation of African history.

### Core Components
- **`AfricanManuscriptTranscriber`**: An AI-powered service designed to transcribe handwritten documents in multiple African languages.
- **`MetadataManager`**: A service for creating rich, multilingual, and searchable metadata for every document in the archive.
- **Ingestion Pipeline**: A workflow that orchestrates the transcription and metadata creation process for newly digitized documents.

---
