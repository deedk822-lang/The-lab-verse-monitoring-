# 📚 Vaal AI Empire - API Reference

Complete API documentation for the Rainmaker Orchestrator system.

---

## Table of Contents

1. [Core Classes](#core-classes)
2. [Tool Types](#tool-types)
3. [Directive Syntax](#directive-syntax)
4. [Python API](#python-api)
5. [REST API](#rest-api)
6. [Response Formats](#response-formats)
7. [Error Handling](#error-handling)
8. [Rate Limits](#rate-limits)

---

## Core Classes

### RainmakerOrchestrator

Main orchestrator class for executing directives.

```python
class RainmakerOrchestrator:
    def __init__(self, config_file: str = ".env")
    async def execute_directive(self, directive: str) -> DirectiveResult
    async def batch_execute(self, directives: List[str]) -> List[DirectiveResult]
    async def close(self)
```

#### Methods

**`__init__(config_file: str = ".env")`**
- Initializes the orchestrator with configuration
- Parameters:
  - `config_file`: Path to environment configuration file
- Raises: None (logs warnings for missing config)

**`execute_directive(directive: str) -> DirectiveResult`**
- Executes a single natural language directive
- Parameters:
  - `directive`: Natural language command string
- Returns: `DirectiveResult` object
- Raises: None (errors captured in result)

**`batch_execute(directives: List[str]) -> List[DirectiveResult]`**
- Executes multiple directives concurrently
- Parameters:
  - `directives`: List of directive strings
- Returns: List of `DirectiveResult` objects
- Raises: None

**`close()`**
- Cleanup and close connections
- Parameters: None
- Returns: None

#### Example

```python
import asyncio
from rainmaker_orchestrator import RainmakerOrchestrator

async def main():
    orchestrator = RainmakerOrchestrator()

    # Single execution
    result = await orchestrator.execute_directive("Analyze project history")
    print(f"Success: {result.success}")

    # Batch execution
    results = await orchestrator.batch_execute([
        "grok Search for AI news",
        "linear Create task: Update docs"
    ])

    await orchestrator.close()

asyncio.run(main())
```

---

### DirectiveResult

Result object from directive execution.

```python
@dataclass
class DirectiveResult:
    success: bool
    tool: str
    response: Any
    execution_time: float
    error: Optional[str] = None
```

#### Fields

- **`success`** (bool): Whether execution succeeded
- **`tool`** (str): Tool that was used (e.g., "kimi", "gemini")
- **`response`** (Any): Response data from the tool
- **`execution_time`** (float): Execution duration in seconds
- **`error`** (Optional[str]): Error message if failed

#### Example

```python
result = await orchestrator.execute_directive("Analyze data")

if result.success:
    print(f"Completed in {result.execution_time:.2f}s")
    print(f"Response: {result.response}")
else:
    print(f"Error: {result.error}")
```

---

### DirectiveParser

Parses natural language into structured commands.

```python
class DirectiveParser:
    @classmethod
    def parse(cls, directive: str) -> tuple[ToolType, str]
```

#### Methods

**`parse(directive: str) -> tuple[ToolType, str]`**
- Parses directive into tool type and prompt
- Parameters:
  - `directive`: Natural language directive
- Returns: Tuple of (ToolType, cleaned_prompt)

#### Example

```python
from rainmaker_orchestrator import DirectiveParser, ToolType

# Implicit routing
tool, prompt = DirectiveParser.parse("Analyze project history")
# Returns: (ToolType.KIMI_LINEAR, "Analyze project history")

# Explicit routing
tool, prompt = DirectiveParser.parse("gemini Translate this text")
# Returns: (ToolType.GEMINI_PRO, "Translate this text")
```

---

### ToolExecutor

Executes commands on specific AI tools.

```python
class ToolExecutor:
    def __init__(self, config: ConfigManager)
    async def execute(self, tool: ToolType, prompt: str) -> DirectiveResult
```

#### Methods

**`execute(tool: ToolType, prompt: str) -> DirectiveResult`**
- Executes prompt on specified tool
- Parameters:
  - `tool`: ToolType enum value
  - `prompt`: Prompt string
- Returns: DirectiveResult object

---

### ConfigManager

Manages API keys and configuration.

```python
class ConfigManager:
    def __init__(self, config_file: str = ".env")
    def get(self, key: str, default: str = '') -> str
    def validate(self) -> List[str]
```

#### Methods

**`get(key: str, default: str = '') -> str`**
- Retrieves configuration value
- Parameters:
  - `key`: Configuration key
  - `default`: Default value if not found
- Returns: Configuration value

**`validate() -> List[str]`**
- Validates required configuration
- Returns: List of missing keys

---

## Tool Types

Available AI tools in the ecosystem.

```python
class ToolType(Enum):
    KIMI_LINEAR = "kimi"
    GEMINI_PRO = "gemini"
    GROK = "grok"
    COHERE = "cohere"
    PERPLEXITY = "perplexity"
    ATLAS_TV = "atlas"
    LINEAR = "linear"
    VLLM = "vllm"
```

### Tool Capabilities

| Tool | Capabilities | Use Cases |
|------|-------------|-----------|
| **Kimi Linear** | 1M context, strategic analysis | Project history, roadmaps, technical debt |
| **Gemini Pro** | Vision, audio, multilingual | Image analysis, translation, multimodal tasks |
| **Grok** | Real-time web data | News search, trending topics, current events |
| **Cohere** | Classification, ranking | Lead filtering, semantic search, sentiment |
| **Perplexity** | Research, citations | Patent search, legal research, fact-checking |
| **Atlas TV** | Ad generation | TV commercials, broadcast content |
| **Linear** | Project management | Task creation, issue tracking, roadmaps |

---

## Directive Syntax

### Implicit Tool Selection

The orchestrator automatically routes based on keywords:

```python
# Routes to Kimi Linear
"Analyze project history"
"Generate roadmap for Q4"
"Review technical debt"

# Routes to Gemini Pro
"Translate this document to French"
"Analyze this image"
"Describe this photo"

# Routes to Grok
"Search for latest AI news"
"What's trending on X?"
"Find recent developments in quantum computing"

# Routes to Cohere
"Filter these leads by quality"
"Classify sentiment of these reviews"
"Rerank these search results"

# Routes to Perplexity
"Check for patent conflicts on: AI scheduler"
"Research prior art for: blockchain voting"
"Legal analysis of: data privacy laws"

# Routes to Atlas TV
"Generate 30-second TV ad for: Tesla Model Y"
"Create broadcast commercial for: Nike shoes"

# Routes to Linear
"Create task: Implement OAuth"
"Track issue: Login page crashes"
"Add ticket: Update dependencies"
```

### Explicit Tool Selection

Prefix with tool name for direct routing:

```python
# Explicit Kimi
"kimi Using your 1M context, analyze entire codebase"

# Explicit Gemini
"gemini Translate this technical manual to Sesotho"

# Explicit Grok
"grok Find tweets about our product launch"

# Explicit Perplexity
"perplexity Search patents for: autonomous vehicle navigation"

# Explicit Linear
"linear Create epic: User authentication system"
```

### Skip to Content

Use `[Skip to content]` to bypass preamble:

```python
"[Skip to content] Analyze financial data from Q3"
```

---

## Python API

### Basic Usage

```python
import asyncio
from rainmaker_orchestrator import RainmakerOrchestrator

async def basic_example():
    orchestrator = RainmakerOrchestrator()

    result = await orchestrator.execute_directive(
        "Analyze our technical debt"
    )

    if result.success:
        print(result.response)

    await orchestrator.close()

asyncio.run(basic_example())
```

### Advanced Usage

```python
import asyncio
from rainmaker_orchestrator import (
    RainmakerOrchestrator,
    DirectiveParser,
    ToolType
)

async def advanced_example():
    orchestrator = RainmakerOrchestrator()

    # Custom directive parsing
    tool, prompt = DirectiveParser.parse("custom directive")
    print(f"Will route to: {tool}")

    # Batch execution with error handling
    directives = [
        "grok Latest AI news",
        "perplexity Check patent: ML scheduler",
        "linear Create task: Add tests"
    ]

    results = await orchestrator.batch_execute(directives)

    for directive, result in zip(directives, results):
        if result.success:
            print(f"✓ {directive}: {result.execution_time:.2f}s")
        else:
            print(f"✗ {directive}: {result.error}")

    await orchestrator.close()

asyncio.run(advanced_example())
```

### Context Manager Pattern

```python
import asyncio
from rainmaker_orchestrator import RainmakerOrchestrator

class AsyncOrchestrator(RainmakerOrchestrator):
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

async def context_example():
    async with AsyncOrchestrator() as orch:
        result = await orch.execute_directive("Analyze data")
        print(result.response)

asyncio.run(context_example())
```

---

## REST API

### Running the API Server

```bash
# Start API server
python -m uvicorn api.server:app --host 0.0.0.0 --port 8080

# With Docker
docker-compose up orchestrator
```

### Endpoints

#### POST /directive

Execute a single directive.

**Request:**
```json
{
  "directive": "Analyze project history",
  "timeout": 120
}
```

**Response:**
```json
{
  "success": true,
  "tool": "kimi",
  "response": {
    "analysis": "...",
    "recommendations": [...]
  },
  "execution_time": 3.45,
  "error": null
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8080/directive \
  -H "Content-Type: application/json" \
  -d '{"directive": "Analyze project history"}'
```

#### POST /batch

Execute multiple directives concurrently.

**Request:**
```json
{
  "directives": [
    "grok Latest AI news",
    "linear Create task: Update docs"
  ]
}
```

**Response:**
```json
{
  "results": [
    {
      "success": true,
      "tool": "grok",
      "response": {...},
      "execution_time": 2.1
    },
    {
      "success": true,
      "tool": "linear",
      "response": {...},
      "execution_time": 1.8
    }
  ],
  "total_time": 2.1
}
```

#### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "services": {
    "vllm": "up",
    "qdrant": "up",
    "prometheus": "up"
  }
}
```

#### GET /tools

List available tools.

**Response:**
```json
{
  "tools": [
    {
      "name": "kimi",
      "type": "KIMI_LINEAR",
      "capabilities": ["analysis", "1M context"],
      "status": "available"
    },
    ...
  ]
}
```

---

## Response Formats

### Kimi Linear Response

```json
{
  "choices": [{
    "text": "Analysis results...",
    "finish_reason": "stop",
    "logprobs": null
  }],
  "usage": {
    "prompt_tokens": 150,
    "completion_tokens": 850,
    "total_tokens": 1000
  }
}
```

### Gemini Pro Response

```json
{
  "candidates": [{
    "content": {
      "parts": [{"text": "Translation..."}],
      "role": "model"
    },
    "finishReason": "STOP",
    "safetyRatings": [...]
  }],
  "usageMetadata": {
    "promptTokenCount": 50,
    "candidatesTokenCount": 200
  }
}
```

### Grok Response

```json
{
  "choices": [{
    "message": {
      "role": "assistant",
      "content": "Search results..."
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 100,
    "completion_tokens": 300
  }
}
```

### Linear Response

```json
{
  "data": {
    "issueCreate": {
      "success": true,
      "issue": {
        "id": "PROJ-123",
        "title": "Task title",
        "url": "https://linear.app/team/issue/PROJ-123",
        "state": {
          "name": "Todo"
        }
      }
    }
  }
}
```

---

## Error Handling

### Error Types

```python
# API errors
{
  "success": false,
  "error": "API key invalid",
  "tool": "gemini",
  "execution_time": 0.5
}

# Timeout errors
{
  "success": false,
  "error": "Request timeout after 120s",
  "tool": "kimi",
  "execution_time": 120.0
}

# Network errors
{
  "success": false,
  "error": "Connection refused to http://localhost:8000",
  "tool": "vllm",
  "execution_time": 1.2
}

# Validation errors
{
  "success": false,
  "error": "Directive cannot be empty",
  "tool": null,
  "execution_time": 0.0
}
```

### Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

class RetryableOrchestrator(RainmakerOrchestrator):
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def execute_with_retry(self, directive: str):
        return await self.execute_directive(directive)

# Usage
orchestrator = RetryableOrchestrator()
result = await orchestrator.execute_with_retry("Analyze data")
```

---

## Rate Limits

### Per-Tool Limits

| Tool | Requests/Min | Requests/Hour | Tokens/Min |
|------|--------------|---------------|------------|
| Kimi Linear | 60 | 1000 | 100K |
| Gemini Pro | 60 | 1500 | 32K |
| Grok | 50 | 500 | 16K |
| Cohere | 100 | 5000 | 40K |
| Perplexity | 20 | 200 | 10K |
| Linear | 100 | 5000 | N/A |

### Rate Limit Headers

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1640995200
```

### Handling Rate Limits

```python
import asyncio
from rainmaker_orchestrator import RainmakerOrchestrator

async def rate_limited_execution():
    orchestrator = RainmakerOrchestrator()

    results = []
    for i in range(100):
        try:
            result = await orchestrator.execute_directive(f"Query {i}")
            results.append(result)
        except Exception as e:
            if "rate limit" in str(e).lower():
                print("Rate limited, waiting 60s...")
                await asyncio.sleep(60)
                result = await orchestrator.execute_directive(f"Query {i}")
                results.append(result)

    await orchestrator.close()
    return results
```

---

## Code Examples

### Multi-Tool Workflow

```python
async def multi_tool_workflow():
    """Execute complex multi-step workflow"""
    orchestrator = RainmakerOrchestrator()

    # Step 1: Research with Perplexity
    research = await orchestrator.execute_directive(
        "perplexity Research latest AI frameworks"
    )

    # Step 2: Analyze with Kimi
    analysis = await orchestrator.execute_directive(
        f"kimi Analyze this research: {research.response}"
    )

    # Step 3: Create tasks in Linear
    for recommendation in analysis.response.get('recommendations', []):
        await orchestrator.execute_directive(
            f"linear Create task: {recommendation}"
        )

    await orchestrator.close()
```

### Streaming Responses

```python
async def stream_response():
    """Stream large responses"""
    orchestrator = RainmakerOrchestrator()

    # For large context analysis
    result = await orchestrator.execute_directive(
        "kimi Analyze entire repository history"
    )

    # Stream response in chunks
    response_text = result.response['choices'][0]['text']
    chunk_size = 100

    for i in range(0, len(response_text), chunk_size):
        chunk = response_text[i:i+chunk_size]
        print(chunk, end='', flush=True)
        await asyncio.sleep(0.1)  # Simulate streaming

    await orchestrator.close()
```

---

**Built in the Vaal. Built for Africa. Built to dominate.**