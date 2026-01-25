from __future__ import annotations

import json
import logging
import re

from agent.config import config
from agent.tools.llm_provider import llm_provider
from vaal_ai_empire.api.sanitizers import sanitize_prompt

logger = logging.getLogger(__name__)


async def run_diagnostic(state):
    """Analyze pipeline failure using configured LLM provider (Z.AI, Qwen, or Hugging Face).

    Works with Z.AI API, Qwen/Dashscope API, or local Hugging Face models.
    No model download needed for API providers - uses your existing keys!
    """

    logger.info(
        "🔍 Diagnosing pipeline (using %s) - run_id=%s",
        config.llm_provider.upper(),
        getattr(state, "run_id", "unknown"),
    )

    sanitized_repo = sanitize_prompt(getattr(state, 'repo_full_name', 'unknown'))
    sanitized_branch = sanitize_prompt(getattr(state, 'branch', 'unknown'))
    sanitized_workflow = sanitize_prompt(getattr(state, 'workflow_name', 'unknown'))
    sanitized_error = sanitize_prompt(getattr(state, 'error_message', 'unknown'))
    sanitized_logs = sanitize_prompt(
        (getattr(state, 'logs', '')[:2000] if isinstance(getattr(state, 'logs', ''), str) else str(getattr(state, 'logs', ''))[:2000])
    )

    diagnostic_prompt = f"""Analyze this pipeline failure and provide structured JSON analysis:

Repository: {sanitized_repo}
Branch: {sanitized_branch}
Workflow: {sanitized_workflow}
Error: {sanitized_error}

Failed Jobs:
{sanitize_prompt(json.dumps(getattr(state, 'failed_jobs', []), indent=2))}

Pipeline Logs:
{sanitized_logs}

Provide ONLY valid JSON in this format:
{{
  "root_cause": "Clear, specific cause of failure",
  "confidence": 0.95,
  "fix_category": "dependency|test|config|security|timeout|network",
  "recommended_action": "Specific action to fix",
  "monitoring_specific": "Any monitoring stack specific notes"
}}

Respond ONLY with valid JSON, no other text."""

    try:
        # Use the configured LLM provider
        logger.info("🤖 Running diagnosis with %s...", config.llm_provider)
        response = await llm_provider.inference("diagnostic", diagnostic_prompt, max_tokens=1024)

        # Extract JSON from response
        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if not json_match:
            logger.error("❌ No JSON found in response")
            raise ValueError("Model did not return valid JSON")

        analysis = json.loads(json_match.group())

        # Map back to state
        if hasattr(state, "root_cause"):
            state.root_cause = analysis.get("root_cause", "Unknown cause")
        if hasattr(state, "confidence_score"):
            state.confidence_score = analysis.get("confidence", 0.5)

        logger.info("✅ Diagnosis complete")
        logger.info("   Root cause: %s", state.root_cause if hasattr(state, "root_cause") else "")
        logger.info(
            "   Confidence: %.1f%%", (state.confidence_score * 100) if hasattr(state, "confidence_score") else 0
        )

        return state

    except Exception as e:
        logger.error("❌ Diagnostic failed: %s", e)
        raise
