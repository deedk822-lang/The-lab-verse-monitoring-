# Rainmaker AI Superstack - Production Ready

A production-ready AI orchestration system with self-healing code generation, multi-model routing, and secure file operations.

## 🎯 What This Actually Does

**Real Capabilities** (No Mock-ups):

✅ **Self-Healing Code Generation** - Generates Python code, tests it, and auto-fixes errors
✅ **Multi-Model Routing** - Routes tasks to Kimi (Moonshot AI) or Ollama automatically
✅ **Secure File Operations** - Sandboxed workspace with path traversal protection
✅ **Production HTTP API** - Flask + Gunicorn with proper error handling
✅ **Resource Limits** - Memory and timeout limits for script execution
✅ **Lab-Verse Integration** - Connects to your monitoring ecosystem

## 🏗️ Architecture

```
HTTP Request → Node.js TaskRouter → Orchestrator
                                      ↓
                          ┌───────────┴───────────┐
                          ↓                       ↓
                    Kimi (Moonshot AI)      Ollama (Local)
                          ↓                       ↓
                     Blueprint (JSON)      Blueprint (JSON)
                          ↓                       ↓
                          └───────────┬───────────┘
                                      ↓
                              Confidence Engine
                                (Governance)
                                      ↓
            ┌─────────────────────────┼────────────────────────┐
            ↓                         ↓                        ↓
      Auto-Merge (>=90)      Pull Request (>=70)           Reject (<70)
```

### 🛡️ Governance Model: The Confidence Engine

This system is governed by a **Confidence Engine** that quantifies the risk of every proposed code change. It's an automated SRE (Site Reliability Engineer) that decides whether an AI-generated change is safe enough to merge automatically.

#### How it Works

1.  **Blueprint Analysis**: Every proposed change (a "blueprint") from the AI is analyzed.
2.  **Risk Scoring**: The `ConfidenceScorer` calculates a score from 0 to 100 based on several factors:
    *   **Protected Paths**: Touching critical infrastructure files (like `.github/workflows` or `docker-compose.yml`) severely penalizes the score.
    *   **Complexity**: Large, complex changes (measured by lines of code) receive a lower score.
    *   **Security Risks**: A static analysis scan looks for potential vulnerabilities. Any findings reduce the score.
    *   **Test Coverage**: Blueprints that include new or updated tests get a score bonus.
3.  **Decision Matrix**: Based on the final score, the system takes one of three actions:
    *   **A (90-100)**: **Auto-Merge**. The change is considered safe and is automatically merged and deployed.
    *   **B (70-89)**: **Human Review**. The change is submitted as a pull request, requiring a human engineer to approve it.
    *   **C (<70)**: **Reject**. The task is rejected, and the AI is notified to reconsider its approach.

This governance layer ensures that while the system is autonomous, it operates with a "safety-first" mindset, preventing risky or broken code from ever reaching production without oversight.

### 🤖 Automated Governance with Jules

All pull requests in this repository are automatically reviewed by **Jules**, our autonomous DevOps guardian. This process ensures that every change meets our quality and security standards before it can be merged.

**How it Works:**

1.  **PR Analysis:** When a pull request is created, the "Jules Governance" workflow is triggered.
2.  **Confidence Score:** Jules analyzes the changes and calculates a "confidence score" based on a set of rules.
3.  **PR Comment:** The results of the analysis are posted as a comment on the pull request, providing immediate feedback.

A pull request will be blocked from merging if it modifies protected files or if its confidence score is below 85. For a detailed breakdown of the rules and how to interact with Jules, please see the [**`AGENTS.md`**](./AGENTS.md) file.

### Core Components

- **router.js** - The core orchestration logic with the Confidence Engine.
- **governance/scorer.js** - The ConfidenceScorer that calculates the risk score.
- **scripts/validate.sh** - The validation pipeline that runs before any code is committed.
- **agents/healer.py** - The self-healing agent that responds to alerts.
- **server.py** - The Flask HTTP API that exposes the orchestrator and the alert webhook.

## 📋 Prerequisites

- Docker Engine 20.10+
- Docker Compose V2
- 8GB+ RAM
- 20GB+ disk space
- **Kimi API Key** (required)
- Ollama (optional, for local models)
- **ghcr.io Credentials**: The ECS instance must be configured with credentials to pull images from the GitHub Container Registry.

## 🚀 Quick Start

### Step 1: Clone Repository

```bash
git clone https://github.com/deedk822-lang/The-lab-verse-monitoring-.git
cd The-lab-verse-monitoring-/rainmaker_orchestrator
```

### Step 2: Configure Environment

```bash
# Copy example configuration
cp .env.example .env

# Edit with your API keys
nano .env
```

**Required Configuration:**

```bash
KIMI_API_KEY=your_actual_kimi_api_key_here
```

**Optional but Recommended:**

```bash
OLLAMA_API_BASE=http://ollama:11434/api
WORKSPACE_PATH=/workspace
LOG_LEVEL=INFO
GUNICORN_WORKERS=4
```

### Step 3: Build and Run

#### Using Docker (Recommended)

```bash
# Build image
docker build -t rainmaker-orchestrator:latest .

# Run container
docker run -d -p 8080:8080 \
  --name orchestrator \
  -e KIMI_API_KEY=$KIMI_API_KEY \
  -v $(pwd)/workspace:/workspace \
  rainmaker-orchestrator:latest
```

#### Using Docker Compose

```bash
# Start full stack
docker-compose -f ../docker-compose.superstack.yml up -d
```

### Step 4: Verify Deployment

```bash
# Check health
curl http://localhost:8080/health

# Expected response:
# {
#   "status": "healthy",
#   "service": "rainmaker-orchestrator",
#   "version": "2.0.0",
#   "workspace": "/workspace",
#   "configured_models": ["kimi", "ollama"]
# }
```

## 📡 API Endpoints

### Execute Task

Execute an AI task with automatic model routing:

```bash
POST /execute
Content-Type: application/json

{
  "context": "Your task description or prompt",
  "type": "coding_task",
  "model": "kimi",
  "output_filename": "script.py"
}
```

**Example: Self-Healing Code Generation**

```bash
curl -X POST http://localhost:8080/execute \
  -H "Content-Type: application/json" \
  -d '{
    "context": "Write a Python script that calculates the Fibonacci sequence up to n=10 and prints it.",
    "type": "coding_task",
    "output_filename": "fibonacci.py"
  }'
```

**Response (Success):**

```json
{
  "result": {
    "status": "success",
    "final_code_path": "fibonacci.py",
    "output": "0 1 1 2 3 5 8 13 21 34",
    "retries": 0,
    "explanation": "Generated Fibonacci sequence calculator"
  },
  "status": "success",
  "request_id": "abc-123"
}
```

**What Actually Happens:**

1. Orchestrator routes to Kimi API
2. Kimi generates Python code (JSON format)
3. Code is written to workspace as `fibonacci.py`
4. FileSystem Agent executes the script in sandboxed environment
5. If it fails → Error is sent back to Kimi → Regenerates fixed code
6. Retries up to 3 times until code executes successfully
7. Returns final working code and output

### Health Check

```bash
GET /health
```

**Response:**

```json
{
  "status": "healthy",
  "service": "rainmaker-orchestrator",
  "version": "2.0.0",
  "workspace": "/workspace",
  "configured_models": ["kimi", "ollama"]
}
```

### List Workspace Files

```bash
GET /workspace/files
```

**Response:**

```json
{
  "files": [
    {
      "name": "fibonacci.py",
      "size": 542,
      "modified": 1704483600.0
    }
  ],
  "count": 1,
  "workspace": "/workspace"
}
```

### Get File Content

```bash
GET /workspace/files/fibonacci.py
```

**Response:**

```json
{
  "filename": "fibonacci.py",
  "content": "def fibonacci(n):\n    ...",
  "status": "success"
}
```

### Metrics (Prometheus)

```bash
GET /metrics
```

## 🔧 Configuration

### Model Routing Logic

The orchestrator automatically routes tasks based on model preference:

```python
# Automatic routing
if "ollama" in task.get("model", "").lower():
    route_to_ollama()  # Local inference
else:
    route_to_kimi()    # Cloud API (default)
```

### Security Features

✅ **Path Traversal Protection** - All filenames sanitized with `secure_filename()`
✅ **File Size Limits** - Max 10MB per file (configurable)
✅ **Memory Limits** - Script execution limited to 128MB (configurable)
✅ **Timeout Limits** - Scripts killed after 10s (configurable)
✅ **Sandboxed Execution** - Scripts run in isolated workspace

### Resource Limits

Configure in `.env`:

```bash
MAX_FILE_SIZE=10485760        # 10MB max file size
SCRIPT_TIMEOUT=10             # 10 second timeout
SCRIPT_MEMORY_LIMIT=128       # 128MB memory limit
```

## 🧪 Testing

### Test Self-Healing Code Generation

```bash
# Test with intentionally broken prompt
curl -X POST http://localhost:8080/execute \
  -H "Content-Type: application/json" \
  -d '{
    "context": "Write a Python script that divides 10 by user input. Handle division by zero.",
    "type": "coding_task",
    "output_filename": "divide.py"
  }'
```

The orchestrator will:
1. Generate code
2. Test it
3. If it crashes, send error back to AI
4. AI fixes the code
5. Retries until it works (max 3 attempts)

### Test Multiple Concurrent Requests

```bash
# Run 10 concurrent requests
for i in {1..10}; do
  curl -X POST http://localhost:8080/execute \
    -H "Content-Type: application/json" \
    -d '{
      "context": "Print hello world '$i'",
      "type": "coding_task",
      "output_filename": "hello'$i'.py"
    }' &
done
wait
```

All requests should complete successfully.

### Load Testing

```bash
# Install k6
brew install k6  # macOS

# Run load test
k6 run - <<EOF
import http from 'k6/http';
import { check } from 'k6';

export let options = {
  stages: [
    { duration: '30s', target: 10 },
    { duration: '1m', target: 20 },
    { duration: '30s', target: 0 },
  ],
};

export default function() {
  let payload = JSON.stringify({
    context: 'Write a Python script that prints "Hello from k6"',
    type: 'coding_task',
    output_filename: 'test.py'
  });

  let params = {
    headers: { 'Content-Type': 'application/json' },
  };

  let res = http.post('http://localhost:8080/execute', payload, params);

  check(res, {
    'status is 200': (r) => r.status === 200,
    'has result': (r) => r.json('result') !== null,
  });
}
EOF
```

## 🔗 Lab-Verse Integration

This orchestrator integrates with the broader Lab-Verse monitoring ecosystem:

### Integration Points

```
Rainmaker Orchestrator
        ↓
    Lab-Verse API Gateway (Port 8080)
        ↓
    ┌───────────────────────────────────┐
    │  Platform Integrations:           │
    │  - Grafana (Metrics)              │
    │  - HuggingFace (Models)           │
    │  - DataDog (APM)                  │
    │  - HubSpot (CRM)                  │
    │  - Confluence (Docs)              │
    │  - ClickUp (Tasks)                │
    │  - CodeRabbit (Code Review)       │
    └───────────────────────────────────┘
```

### Enable Full Integration

1. Set Lab-Verse environment variables in `.env`:

```bash
GRAFANA_API_KEY=your_key
HF_TOKEN=your_token
DATADOG_API_KEY=your_key
# ... etc
```

2. Deploy with full stack:

```bash
cd ..
docker-compose -f docker-compose.production.yml up -d
```

3. Access unified dashboard:

```
https://localhost
```

## 🚧 Troubleshooting

### Orchestrator Won't Start

```bash
# Check logs
docker logs orchestrator

# Common issues:
# 1. Missing KIMI_API_KEY
echo $KIMI_API_KEY

# 2. Port already in use
lsof -i :8080

# 3. Workspace permission denied
ls -la /workspace
```

### API Returns "KIMI_API_KEY is not set"

**Fix:**

```bash
# Verify key is in .env
cat .env | grep KIMI_API_KEY

# Restart container with key
docker stop orchestrator
docker rm orchestrator
docker run -d -p 8080:8080 \
  -e KIMI_API_KEY=your_actual_key_here \
  --name orchestrator \
  rainmaker-orchestrator:latest
```

### Code Generation Fails After Max Retries

**Possible causes:**

1. **Prompt too vague** - Be more specific
2. **Task too complex** - Break into smaller tasks
3. **Model limitations** - Try different model
4. **API rate limits** - Wait and retry

**Debug:**

```bash
# Check detailed error
curl -X POST http://localhost:8080/execute \
  -H "Content-Type: application/json" \
  -d '{...}' | jq '.result.last_error'
```

### High Memory Usage

**Fix:**

```bash
# Reduce workers
docker stop orchestrator
docker run -d -p 8080:8080 \
  -e GUNICORN_WORKERS=2 \
  -e KIMI_API_KEY=$KIMI_API_KEY \
  rainmaker-orchestrator:latest
```

## 📊 Performance Metrics

### Expected Performance

- **Request Latency**: 2-10 seconds (AI generation + execution)
- **Concurrent Capacity**: 4 workers = 4 simultaneous tasks
- **Memory Usage**: ~512MB per worker
- **Success Rate**: >95% for well-defined prompts

### Optimization Tips

1. **Use Ollama for speed** - Local inference is 10x faster than API
2. **Increase workers** - More workers = more concurrency
3. **Tune timeouts** - Increase for complex tasks
4. **Cache results** - Store frequently used code

## 🔒 Security

### Production Checklist

- [ ] KIMI_API_KEY set (not placeholder)
- [ ] FLASK_DEBUG=false
- [ ] Workspace directory permissions set (chmod 700)
- [ ] Resource limits configured
- [ ] Running as non-root user in Docker
- [ ] HTTPS enabled (if exposed to internet)
- [ ] Rate limiting configured
- [ ] Monitoring alerts set up

### Security Best Practices

✅ All file operations use `secure_filename()`
✅ Scripts run with memory/timeout limits
✅ Workspace isolated from host filesystem
✅ No code execution outside sandbox
✅ API keys stored in environment variables
✅ Logs don't contain sensitive data

## 📝 License

MIT License - See [LICENSE](../LICENSE) file for details.

## 🆘 Support

- **GitHub Issues**: [Create an issue](https://github.com/deedk822-lang/The-lab-verse-monitoring-/issues)
- **Documentation**: See `docs/` directory
- **Logs**: `docker logs orchestrator`

---

**Made with ❤️ by the Rainmaker team - Production Ready, No Mock-ups!**
## Package Structure

This project uses src-layout for proper packaging:

```
repo-root/
├── src/
│   └── rainmaker_orchestrator/  # Main package
│       ├── core/                # Core orchestration logic
│       ├── agents/              # Self-healing agents
│       └── clients/             # API clients
├── agents/                      # Standalone agent services
├── api/                         # REST API layer
└── pyproject.toml               # Package configuration
```

Install in editable mode: `pip install -e .[dev,test]`
