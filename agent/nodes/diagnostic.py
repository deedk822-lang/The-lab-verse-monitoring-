from __future__ import annotations

import json
import logging
import re

from agent.config import config
from agent.tools.hf_model_loader import model_loader
from vaal_ai_empire.api.sanitizers import sanitize_prompt

logger = logging.getLogger(__name__)


async def run_diagnostic(state):
    """Analyze pipeline failure using a local Hugging Face model.

    Note: This expects the existing Bitbucket MCP integration in your codebase.
    """

    logger.info("🔍 Diagnosing pipeline run_id=%s", getattr(state, "run_id", "unknown"))

    # Sanitize inputs to prevent prompt injection
    repo_name = sanitize_prompt(str(getattr(state, 'repo_full_name', 'unknown')), max_length=200)
    branch = sanitize_prompt(str(getattr(state, 'branch', 'unknown')), max_length=200)
    workflow = sanitize_prompt(str(getattr(state, 'workflow_name', 'unknown')), max_length=200)
    error_msg = sanitize_prompt(str(getattr(state, 'error_message', 'unknown')), max_length=1000)

    diagnostic_prompt = f"""Analyze this pipeline failure and provide structured JSON analysis:

Repository: {repo_name}
Branch: {branch}
Workflow: {workflow}
Error: {error_msg}

"""

    failed_jobs = getattr(state, "failed_jobs", [])
    logs = getattr(state, "logs", "")

    # Sanitize failed jobs and logs
    sanitized_failed_jobs = sanitize_prompt(json.dumps(failed_jobs, indent=2), max_length=2000)
    sanitized_logs = sanitize_prompt(
        logs[:2000] if isinstance(logs, str) else str(logs)[:2000],
        max_length=2000
    )

    diagnostic_prompt += f"""Failed Jobs:
{sanitized_failed_jobs}

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

    await model_loader.load_model(config.hf.model_diagnostic, task="diagnostic")
    response = await model_loader.inference("diagnostic", diagnostic_prompt, max_tokens=1024)

    json_match = re.search(r"\{.*\}", response, re.DOTALL)
    if not json_match:
        raise ValueError("Model did not return valid JSON")

    analysis = json.loads(json_match.group())

    # Map back to common fields if they exist
    if hasattr(state, "root_cause"):
        state.root_cause = analysis.get("root_cause")
    if hasattr(state, "confidence_score"):
        state.confidence_score = analysis.get("confidence", 0.5)

    model_loader.unload_model("diagnostic")
    return state
