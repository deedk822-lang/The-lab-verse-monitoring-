# AI Connections & Intelligent Router

## Overview

This implementation provides the missing AI connection component for The Lab Verse Monitoring system, based on the **Final Blueprint for Autonomous Authority and Impact Engine**.

## Core Features

### 1. Multi-Model AI Integration

The system integrates multiple AI providers with automatic fallback mechanisms:

-   **Mistral AI Models (Primary):**
    -   `Pixtral-12B-2409`: Multimodal vision + language model (*Visionary Judge*)
    -   `Codestral`: Code generation and analysis (*Operator Judge*)
    -   `Mixtral-8x22B`: Large-scale reasoning (*Auditor Judge*)
-   **Supporting Models:**
    -   `Claude` (Anthropic): *Arbiter* and *Challenger Judge*
    -   `Gemini` (Google): *Fact-Checker Judge #1*
    -   `Groq` (Llama): *Fact-Checker Judge #2*
-   **Fallback Model:**
    -   `GLM-4`: Fallback model for resilience

### 2. "Never-Fail" Workflow

Implements automatic fallback mechanism:

-   Primary model attempts generation.
-   On failure, automatically falls back to GLM-4.
-   Ensures system resilience and 99.9% uptime.

### 3. Multi-Judge Fact-Checking Protocol

Eliminates hallucinations through consensus-based verification:

-   **3 Independent Judges:** Each evaluates claims independently.
-   **Consensus Protocol:** Requires 2/3 agreement for verification.
-   **Evidence Transparency:** Provides source URLs and reasoning.
-   **Structured Output:** Markdown evidence blocks for judges.

### 4. Judge Roles

Four specialized judge roles for comprehensive evaluation:

| Role        | Model            | Purpose                                            |
| :---------- | :--------------- | :------------------------------------------------- |
| **Visionary** | `Pixtral-12B`    | Forward-thinking analysis, innovation focus        |
| **Operator**  | `Codestral`      | Practical implementation, technical feasibility    |
| **Auditor**   | `Mixtral-8x22B`  | Rigorous scrutiny, compliance, risk assessment     |
| **Challenger**| `Claude`         | Critical evaluation, identifies weaknesses       |

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

-   **Endpoint:** `POST /api/ai/intelligent-router?action=generate`
-   **Request:**
    ```json
    {
      "prompt": "Explain quantum computing",
      "primaryModel": "mixtral-8x22b-instruct",
      "fallbackModel": "glm-4"
    }
    ```
-   **Response:**
    ```json
    {
      "success": true,
      "content": "Quantum computing is...",
      "modelUsed": "mixtral-8x22b-instruct",
      "timestamp": "2025-11-23T02:55:00Z"
    }
    ```

### 2. Generation with Fact-Checking

-   **Endpoint:** `POST /api/ai/intelligent-router?action=generate-with-fact-check`
-   **Request:**
    ```json
    {
      "prompt": "Write about the global AI market size in 2030",
      "enableFactCheck": true
    }
    ```
-   **Response:**
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
          "judgeResults": "[...]",
          "evidenceBlock": "### Fact-Check Evidence..."
        }
      ],
      "factCheckCount": 1,
      "timestamp": "2025-11-23T02:55:00Z"
    }
    ```

## Setup Instructions

### 1. Environment Variables

Copy `.env.example` to `.env.local` and configure your API keys:

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

### 2. Install Dependencies & Run

```bash
npm install --ignore-scripts
npm run dev
```

The intelligent router will be available at: `http://localhost:3000/api/ai/intelligent-router`

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
├── .env.local
└── AI_CONNECTIONS_README.md
```
