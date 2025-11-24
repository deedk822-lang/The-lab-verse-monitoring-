# AI Connections & Intelligent Router

## Overview

This implementation provides the missing AI connection component for The Lab Verse Monitoring system, based on the Final Blueprint for Autonomous Authority and Impact Engine.

## Core Features

### 1. Multi-Model AI Integration

The system integrates multiple AI providers with automatic fallback mechanisms:

-   **Mistral AI Models (Primary):**
    -   `Pixtral-12B-2409`: Multimodal vision + language model (Visionary Judge)
    -   `Codestral`: Code generation and analysis (Operator Judge)
    -   `Mixtral-8x22B`: Large-scale reasoning (Auditor Judge)
-   **Supporting Models:**
    -   `Claude (Anthropic)`: Arbiter and Challenger Judge
    -   `Gemini (Google)`: Fact-Checker Judge #1
    -   `Groq (Llama)`: Fact-Checker Judge #2
-   **GLM-4:** Fallback model for resilience

### 2. Never-Fail Workflow

Implements automatic fallback mechanism:

-   Primary model attempts generation
-   On failure, automatically falls back to GLM-4
-   Ensures system resilience and 99.9% uptime

### 3. Multi-Judge Fact-Checking Protocol

Eliminates hallucinations through consensus-based verification:

-   **3 Independent Judges:** Each evaluates claims independently
-   **Consensus Protocol:** Requires 2/3 agreement for verification
-   **Evidence Transparency:** Provides source URLs and reasoning
-   **Structured Output:** Markdown evidence blocks for judges

### 4. Judge Roles

Four specialized judge roles for comprehensive evaluation:

| Role       | Model           | Purpose                                              |
| :--------- | :-------------- | :--------------------------------------------------- |
| Visionary  | Pixtral-12B     | Forward-thinking analysis, innovation focus          |
| Operator   | Codestral       | Practical implementation, technical feasibility      |
| Auditor    | Mixtral-8x22B   | Rigorous scrutiny, compliance, risk assessment       |
| Challenger | Claude          | Critical evaluation, identifies weaknesses           |

## Architecture

```
┌─────────────────────────────────────────────────┐
│         Intelligent Router API                  │
│  /api/ai/intelligent-router?action=...          │
└─────────────────┬───────────────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
   ┌────▼────┐       ┌─────▼──────┐
   │ Generate│       │ Fact-Check │
   │ Content │       │   Claims   │
   └────┬────┘       └─────┬──────┘
        │                  │
   ┌────▼────────┐    ┌───▼──────────────┐
   │  Primary    │    │  3 Judge Agents  │
   │  (Mistral)  │    │  (Parallel Exec) │
   └────┬────────┘    └───┬──────────────┘
        │                  │
   ┌────▼────────┐    ┌───▼──────────────┐
   │  Fallback   │    │  Consensus       │
   │  (GLM-4)    │    │  Protocol        │
   └─────────────┘    └───┬──────────────┘
                           │
                      ┌────▼─────────┐
                      │  Evidence    │
                      │  Block       │
                      └──────────────┘
```

## API Endpoints

### 1. Simple Generation with Fallback

**Endpoint:** `POST /api/ai/intelligent-router?action=generate`

**Request:**

```json
{
  "prompt": "Explain quantum computing",
  "primaryModel": "mixtral-8x22b-instruct",
  "fallbackModel": "glm-4"
}
```

**Response:**

```json
{
  "success": true,
  "content": "Quantum computing is...",
  "modelUsed": "mixtral-8x22b-instruct",
  "timestamp": "2025-11-23T02:55:00Z"
}
```

### 2. Generation with Fact-Checking

**Endpoint:** `POST /api/ai/intelligent-router?action=generate-with-fact-check`

**Request:**

```json
{
  "prompt": "Write about the global AI market size in 2030",
  "enableFactCheck": true
}
```

**Response:**

```json
{
  "success": true,
  "content": "The global AI market... [with evidence blocks appended]",
  "modelUsed": "mixtral-8x22b-instruct",
  "factChecks": [
    {
      "claim": "The global AI market is projected to reach $826B by 2030",
      "finalVerdict": "Fact-Checked: True",
      "consensus": "Consensus: 2/3 judges agree",
      "judgeResults": [...],
      "evidenceBlock": "### Fact-Check Evidence..."
    }
  ],
  "factCheckCount": 1,
  "timestamp": "2025-11-23T02:55:00Z"
}
```

### 3. Standalone Fact-Checking

**Endpoint:** `POST /api/ai/intelligent-router?action=fact-check`

**Request:**

```json
{
  "claim": "The global AI market is projected to reach $826B by 2030",
  "searchResults": [
    "Source 1: MarketWatch reports...",
    "Source 2: Statista shows..."
  ]
}
```

**Response:**

```json
{
  "success": true,
  "claim": "The global AI market is projected to reach $826B by 2030",
  "finalVerdict": "Fact-Checked: True",
  "consensus": "Consensus: 2/3 judges agree",
  "judgeResults": [
    {
      "claim": "...",
      "verdict": "True",
      "confidence": 85,
      "evidence_url": "https://www.marketwatch.com/...",
      "reasoning": "Multiple credible sources confirm...",
      "judge": "Judge Gemini"
    },
    ...
  ],
  "evidenceBlock": "### Fact-Check Evidence for Claim...",
  "timestamp": "2025-11-23T02:55:00Z"
}
```

## Setup Instructions

### 1. Environment Variables

Copy `.env.local` and configure your API keys:

```bash
# Required for core functionality
MISTRAL_API_KEY=your_mistral_api_key
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Optional: Fallback model
GLM_API_KEY=your_glm_api_key
GLM_API_ENDPOINT=https://open.bigmodel.cn/api/paas/v4

# Gateway authentication
GATEWAY_API_KEY=your_secure_gateway_key
```

### 2. Install Dependencies

```bash
cd /home/ubuntu/The-lab-verse-monitoring-
npm install --ignore-scripts
```

### 3. Start Development Server

```bash
npm run dev
```

The intelligent router will be available at:

-   `http://localhost:3000/api/ai/intelligent-router`

### 4. Test the API

```bash
# Test simple generation
curl -X POST http://localhost:3000/api/ai/intelligent-router?action=generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_gateway_key" \
  -d '{
    "prompt": "Explain AI in simple terms"
  }'

# Test fact-checking
curl -X POST http://localhost:3000/api/ai/intelligent-router?action=fact-check \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_gateway_key" \
  -d '{
    "claim": "The Earth orbits the Sun"
  }'
```

## Integration with Existing System

### Airtable Integration

The fact-checked content can be automatically written back to Airtable:

```typescript
import { generateFactCheckedContent } from './src/ai-connections/intelligent-router';

async function processAirtableRecord(recordId: string, prompt: string ) {
  // Generate content with fact-checking
  const result = await generateFactCheckedContent(prompt, true);

  // Write back to Airtable
  await updateAirtableRecord(recordId, {
    content: result.content,
    modelUsed: result.modelUsed,
    factCheckCount: result.factChecks?.length || 0,
    verified: result.success
  });
}
```

### MCP Server Integration

Connect to existing MCP servers for data retrieval:

```typescript
// Fetch data from HuggingFace MCP
const hfData = await mcpClient.call('huggingface', 'search_models', {
  query: 'text-generation'
});

// Use in fact-checking
const factCheck = await factCheckClaim(
  'HuggingFace has over 100,000 models',
  [JSON.stringify(hfData)]
);
```

## File Structure

```
The-lab-verse-monitoring-/
├── src/
│   └── ai-connections/
│       ├── mistral-config.ts        # AI model configurations
│       └── intelligent-router.ts    # Core routing logic
├── pages/
│   └── api/
│       └── ai/
│           └── intelligent-router.ts # API endpoint
├── .env.local                        # Environment variables
└── AI_CONNECTIONS_README.md          # This file
```

## Key Features Implemented

-   [x] Multi-Model Integration: Mistral, Claude, Gemini, Groq, GLM-4
-   [x] Never-Fail Workflow: Automatic fallback mechanism
-   [x] Multi-Judge Fact-Checking: 3 independent judges with consensus
-   [x] Evidence Transparency: Markdown blocks with sources
-   [x] Judge Roles: Visionary, Operator, Auditor, Challenger
-   [x] API Endpoints: Generate, Fact-Check, Combined workflow
-   [x] Authentication: Bearer token support
-   [x] Error Handling: Graceful degradation

## Next Steps

1.  **Configure API Keys:** Add your API keys to `.env.local`
2.  **Test Endpoints:** Use the `curl` examples above
3.  **Deploy to Vercel:** `vercel --prod`
4.  **Monitor Usage:** Check logs for model performance
5.  **Integrate with Airtable:** Connect to your existing workflows

## Troubleshooting

**Issue:** "Unauthorized" error

**Solution:** Ensure `GATEWAY_API_KEY` is set and included in `Authorization` header

**Issue:** Primary model fails

**Solution:** System automatically falls back to GLM-4. Check API key validity.

**Issue:** Fact-checking returns "Inconclusive"

**Solution:** Provide `searchResults` parameter with relevant context

**Issue:** TypeScript errors

**Solution:** Run `npm run typecheck` to identify issues

## Support

For issues or questions:

1.  Check the logs: `tail -f logs/intelligent-router.log`
2.  Review environment variables: `cat .env.local`
3.  Test individual models: Use the standalone endpoints
4.  Consult the main README: `README.md`

## License

MIT License - See `LICENSE` file for details

---

Built with ❤️ for The Lab Verse Monitoring System
