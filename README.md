# 🤖 AI Provider Monitoring - Python Agent Suite

Complete testing and monitoring toolkit for your AI provider infrastructure.

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Available Scripts](#available-scripts)
- [Usage Examples](#usage-examples)
- [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### One-Command Setup

```bash
# Run the quick start script
./quick-start.sh
```

This script provides an interactive menu to run any of the available tools.

---

## 🛠️ Installation

The `quick-start.sh` script handles dependency installation automatically. To install manually:

```bash
pip3 install -r requirements.txt
```

---

## ⚙️ Configuration

Configuration is managed via environment variables.

### Required

- `VERCEL_URL`: The full URL to your Vercel API endpoint.
  - **Default**: `https://the-lab-verse-monitoring.vercel.app/api/research`

### Optional (for Grafana Integration)

- `GRAFANA_CLOUD_PROM_URL`: The remote write URL for your Grafana Cloud Prometheus instance.
- `GRAFANA_CLOUD_PROM_USER`: Your Grafana Cloud Prometheus username.
- `GRAFANA_CLOUD_API_KEY`: A Grafana Cloud API key with `metrics:write` permissions.

---

## 📜 Available Scripts

### 1. `live_test_agent.py`

A simple agent to send a single query to the endpoint, display the result, and push metrics to Grafana.

**Usage:** `python3 live_test_agent.py "Your prompt here"`

### 2. `test_suite.py`

Runs a comprehensive suite of 8 test cases covering different categories (reasoning, code, math, etc.) and generates a detailed performance report.

**Usage:** `python3 test_suite.py [rate_limit_delay_seconds]`

### 3. `load_test.py`

A powerful load testing tool with three modes:
- `burst`: Send a quick burst of concurrent requests.
- `ramp`: Gradually increase concurrency to find system limits.
- `sustained`: Maintain a constant load for a specified duration.

**Usage:**
- `python3 load_test.py burst <num_requests>`
- `python3 load_test.py ramp <max_concurrent> <step>`
- `python3 load_test.py sustained <concurrent> <duration_seconds>`

### 4. `monitor.py`

A real-time dashboard that continuously polls the endpoint and displays rolling statistics, alerts, and performance ratings.

**Usage:** `python3 monitor.py [interval_seconds]`

### 5. `validate_metrics.py`

Connects to your Grafana Cloud instance to validate that metrics are being received correctly. It checks for data freshness, SLO queries, and provider distribution.

**Usage:** `python3 validate_metrics.py`

---

## 💡 Usage Examples

- **Run a single test:**
  ```bash
  python3 live_test_agent.py "What are the latest AI developments?"
  ```

- **Run the full test suite with a 1-second delay between tests:**
  ```bash
  python3 test_suite.py 1
  ```

- **Simulate 20 concurrent users:**
  ```bash
  python3 load_test.py burst 20
  ```

- **Start the live monitoring dashboard with a 10-second refresh interval:**
  ```bash
  python3 monitor.py 10
  ```

---

## 🔧 Troubleshooting

- **`Python 3 not found`**: Ensure Python 3 is installed and available in your `PATH`.
- **`ModuleNotFoundError`**: Run `pip3 install -r requirements.txt` to install dependencies.
- **Grafana Push Errors**:
  - Verify your `GRAFANA_CLOUD_*` environment variables are correct.
  - Ensure your API key has the necessary permissions.
  - Check for firewalls blocking the connection.
- **Health Check Failed**:
  - Verify the `VERCEL_URL` is correct and the service is deployed and running.
- **Stale Data in Grafana Validator**:
  - Run `live_test_agent.py` or `test_suite.py` to generate new metrics.
  - Wait 30-60 seconds for the metrics to propagate in Grafana Cloud.
