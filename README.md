# Rainmaker AI Superstack

A production-ready, multi-service stack for orchestrating and serving large language models.

## Overview

This repository contains a Docker-based environment for running a sophisticated AI system. It leverages multiple powerful open-source models and tools to provide a comprehensive platform for AI-driven tasks, including a "self-healing" coding agent.

The core of the stack is the **Rainmaker Orchestrator**, a custom Python service that intelligently routes tasks to different AI models and can iteratively test and fix code.

## Services

The stack is defined in `docker-compose.superstack.yml` and includes the following key services:

- **`rainmaker-orchestrator`**: The custom-built "brain" of the operation. It's a Flask-based Python server that accepts tasks, routes them to the appropriate AI model, and manages the execution and verification process.
- **`kimi-linear`**: A powerful, large-context AI model served via `vllm`.
- **`ollama`**: A flexible service for running various open-source models like Llama 3.
- **`open-webui`**: A user-friendly web interface (`ghcr.io/open-webui/open-webui`) that provides a chat-like control panel for interacting with the AI models.
- **`prometheus`**: A monitoring service for collecting metrics from all components.
- **`grafana`**: A visualization dashboard for viewing the metrics collected by Prometheus.

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Git
- An environment with NVIDIA GPUs is required to run the AI models.

### Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/deedk822-lang/The-lab-verse-monitoring-.git
    cd The-lab-verse-monitoring-
    ```

2.  **Configure Environment Variables:**
    Create a `.env` file by copying the example file.
    ```bash
    cp .env.example .env
    ```
    Now, you **must** edit the `.env` file and fill in the required API keys and tokens (e.g., `HF_TOKEN`, `KIMI_API_KEY`, etc.). The system will not work without these secrets.

3.  **Launch the Stack:**
    Use the `docker-compose.superstack.yml` file to build and run all the services in detached mode.
    ```bash
    docker-compose -f docker-compose.superstack.yml up --build -d
    ```

4.  **Access the Services:**
    - **AI Control Panel (Web UI):** `http://localhost:3000`
    - **Grafana Dashboard:** `http://localhost:3001`
    - **Prometheus Metrics:** `http://localhost:9090`
    - **Orchestrator API:** `http://localhost:8080` (e.g., `GET /health`)

## Configuration

All service configurations are managed via the `.env` file at the root of the repository. Key variables include:

- `HF_TOKEN`: Your Hugging Face token, required for downloading models.
- `KIMI_API_KEY`: API key for the Kimi model service.
- `KIMI_API_BASE`: The base URL for the Kimi API endpoint.
- `OLLAMA_API_BASE`: The base URL for the Ollama API endpoint.

## Architecture

The system is designed around a microservices architecture, orchestrated by Docker Compose.

1.  The **Open WebUI** provides the main user interface for sending prompts and tasks.
2.  It is configured to communicate with the **Kimi** and **Ollama** model-serving containers.
3.  For complex, programmatic tasks, a request can be sent to the **Rainmaker Orchestrator** API.
4.  The orchestrator analyzes the task, calls the appropriate model (Kimi or Ollama) to generate code or a solution, and then uses its internal `FileSystemAgent` to write, execute, and validate the output.
5.  **Prometheus** and **Grafana** continuously monitor the health and performance of all services.
