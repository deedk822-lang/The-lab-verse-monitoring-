#!/usr/bin/env python3
"""
GLM-4.7 Senior Architect Agent.
Connects to ZAI API, executes audit, and outputs structured JSON for GitHub Actions.
"""

import os
import sys
import json
import logging
import argparse
import requests
from typing import Dict, Any, Optional

# Configure Structured Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ArchitectAgent")

# Import Prompt
try:
    from config.architect_prompt import ARCHITECT_SYSTEM_PROMPT
except ImportError:
    logger.error("Missing config/architect_prompt.py. Cannot proceed.")
    sys.exit(1)

class ZAIClient:
    """Wrapper for ZAI GLM-4.7 API."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = os.getenv("ZAI_API_BASE", "https://api.z.ai/api/paas/v4")

    def chat_completion(self, prompt: str, context: Optional[str] = None) -> Dict[str, Any]:
        """Sends prompt to GLM-4.7 with thinking mode enabled."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Construct messages
        messages = [{"role": "system", "content": ARCHITECT_SYSTEM_PROMPT}]

        if context:
            messages.append({"role": "system", "content": f"REVIEW CONTEXT:\n{context}"})

        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": "glm-4.7",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 16384,
            "stream": False,
            # Enable Preserved Thinking for complex reasoning
            "extra_body": {
                "enable_thinking": True,
                "clear_thinking": False
            }
        }

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API Request failed: {e}")
            raise

def get_pr_diff(pr_number: int, repo: str, github_token: str) -> str:
    """Fetches the diff for the PR."""
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3.diff"
    }

    logger.info(f"Fetching diff for PR #{pr_number}...")
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.text

def parse_glm_output(result: Dict[str, Any]) -> Dict[str, Any]:
    """Parses GLM output to extract Validation Table and Decision."""
    try:
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")

        # Extract the JSON object from the content
        json_start = content.find("```json")
        json_end = content.rfind("```")

        if json_start != -1 and json_end != -1:
            json_str = content[json_start + 7:json_end]
            parsed_json = json.loads(json_str)
            return {
                "raw_result": content,
                "decision": parsed_json.get("decision", "ERROR"),
                "validation_table": parsed_json.get("validation_table", "Failed to parse table."),
            }
        else:
            raise ValueError("No JSON object found in the output.")

    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Parsing failed: {e}")
        return {"decision": "ERROR", "validation_table": "Failed to parse output", "raw_result": content}

def main(pr_number: int, repo: str, output_file: str):
    try:
        zai_key = os.getenv("ZAI_API_KEY")
        github_token = os.getenv("GITHUB_TOKEN")

        if not zai_key: raise ValueError("ZAI_API_KEY missing")
        if not github_token: raise ValueError("GITHUB_TOKEN missing")

        client = ZAIClient(api_key=zai_key)

        # 1. Get Context (PR Diff)
        pr_diff = get_pr_diff(pr_number, repo, github_token)

        # 2. Construct Audit Prompt
        audit_prompt = f"""
        Perform a Senior Architect Audit on PR #{pr_number} based on the following changes:

        {pr_diff}

        Strictly follow the Output Format and Decision rules defined in your system prompt.
        """

        # 3. Execute Audit (Thinking Mode)
        logger.info("Sending audit request to GLM-4.7...")
        result = client.chat_completion(prompt=audit_prompt, context=pr_diff)

        # 4. Parse Result
        parsed = parse_glm_output(result)

        # 5. Save Output for Workflow
        output_data = {
            "pr_number": pr_number,
            "recommendation": parsed["decision"],
            "validation_table": parsed["validation_table"],
            "raw_result": parsed["raw_result"]
        }

        with open(output_file, "w") as f:
            json.dump(output_data, f, indent=2)

        logger.info(f"Audit complete. Recommendation: {parsed['decision']}")

        # Exit Code 0 for Success/Needs_Work, 1 for Reject/Error
        if parsed["decision"] in ["APPROVE", "NEEDS_WORK"]:
            sys.exit(0)
        else:
            sys.exit(1)

    except Exception as e:
        logger.error(f"Critical Failure: {e}")
        # Write error state to file so GitHub Script doesn't crash
        with open(output_file, "w") as f:
            json.dump({"error": str(e), "recommendation": "ERROR"}, f, indent=2)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Architect Audit")
    parser.add_argument("--pr", type=int, required=True)
    parser.add_argument("--repo", type=str, required=True)
    parser.add_argument("--output", type=str, default="audit_result.json")

    args = parser.parse_args()
    main(args.pr, args.repo, args.output)
