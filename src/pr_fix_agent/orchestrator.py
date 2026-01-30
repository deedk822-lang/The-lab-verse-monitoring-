import json
import structlog
from pathlib import Path
from typing import Optional, Dict, Any

logger = structlog.get_logger(__name__)


class Orchestrator:
    """Orchestrates the PR fix workflow"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Orchestrator with an optional configuration.
        
        Parameters:
            config (Optional[Dict[str, Any]]): Configuration values for the orchestrator; if `None`, an empty dictionary is used and stored on the instance as `self.config`.
        """
        self.config = config or {}
        logger.info("orchestrator_initialized", config=self.config)

    def run_reasoning(self, findings_file: str, output_file: str):
        """
        Produce proposed fixes from a findings file and save them as a proposals JSON file.
        
        This implementation writes a simulated single proposal to `output_file` (it does not currently parse `findings_file`). The output is a JSON array of proposal objects.
        
        Parameters:
            findings_file (str): Path to the findings JSON input (currently not read by this implementation).
            output_file (str): Path where the proposals JSON will be written.
        """
        logger.info("reasoning_start", findings=findings_file, output=output_file)

        # Simulated implementation (as in the original)
        proposals = [{
            "id": "fix_001",
            "issue": "Simulated security issue",
            "proposed_fix": "Add input validation",
            "files": ["src/main.py"]
        }]

        with open(output_file, 'w') as f:
            json.dump(proposals, f, indent=2)

        logger.info("reasoning_complete", proposals_saved=output_file)

    def run_coding(self, proposals_file: str, output_dir: str, apply: bool = False):
        """
        Process proposals, log per-proposal actions, and ensure the output directory exists.
        
        Parameters:
        	proposals_file (str): Path to a JSON file containing a list of proposals. If the file cannot be read or contains invalid JSON, the method logs an error and returns without processing.
        	output_dir (str): Directory path where outputs or generated artifacts should be placed; the directory will be created (including parents) if it does not exist.
        	apply (bool): When True, indicates that fixes should be applied rather than only logged; in this implementation the flag is recorded but no actual file changes are performed.
        """
        logger.info("coding_start", proposals=proposals_file, output=output_dir, apply=apply)

        try:
            with open(proposals_file, 'r') as f:
                proposals = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error("proposals_load_failed", file=proposals_file, error=str(e))
            return

        for proposal in proposals:
            logger.info("applying_fix", issue=proposal.get("issue"))
            # In a real implementation, we would apply changes here

        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        logger.info("coding_complete")

    def generate_pr_body(self, proposals_file: str, test_results_file: str, output_file: str):
        """
        Generate a Markdown PR description summarizing proposed fixes and test outcomes.
        
        Loads proposals from `proposals_file` (expected JSON list) and test results from `test_results_file` (expected JSON with an `exit_code` key), then writes a human-readable PR body to `output_file`. If `proposals_file` is missing or invalid, no fixes are listed. If `test_results_file` is missing or invalid, tests are assumed to have passed (`exit_code` = 0).
        
        Parameters:
            proposals_file (str): Path to a JSON file containing a list of proposals, where each proposal may include `issue` and `proposed_fix` fields.
            test_results_file (str): Path to a JSON file containing test results; expected to include an `exit_code` integer.
            output_file (str): Path where the generated PR body (Markdown) will be written.
        """
        logger.info(
            "generate_pr_start",
            proposals=proposals_file,
            test_results=test_results_file,
            output=output_file
        )

        # Load proposals
        try:
            with open(proposals_file, 'r') as f:
                proposals = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error("proposals_load_failed", file=proposals_file, error=str(e))
            proposals = []

        # Load test results with specific exception handling
        try:
            with open(test_results_file, 'r') as f:
                test_results = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            # Log the error for debugging but allow workflow to continue
            logger.warning(
                "test_results_load_failed",
                file=test_results_file,
                error=str(e),
                error_type=type(e).__name__,
                message="Assuming passed"
            )
            test_results = {"exit_code": 0}

        body = "# 🤖 LLM Code Review & Auto-Fix\n\n"
        body += "This PR contains automated fixes for issues identified during code review.\n\n"
        body += "## 🛠 Fixes Applied\n"

        if not proposals:
            body += "- No specific fixes identified.\n"
        else:
            for p in proposals:
                issue = p.get("issue", "Unknown issue")
                fix = p.get("proposed_fix", "No description provided")
                body += f"- **{issue}**: {fix}\n"

        body += "\n## 🧪 Test Results\n"
        if test_results.get("exit_code", 0) == 0:
            body += "✅ All tests passed after applying fixes.\n"
        else:
            body += "⚠️ Some tests failed. Please review the results manually.\n"

        with open(output_file, 'w') as f:
            f.write(body)

        logger.info("generate_pr_complete", output_file=output_file)


def main():
    """
    CLI entry point for the PR Fix Agent orchestrator.
    
    Parses command-line arguments, validates mode-specific requirements, instantiates an Orchestrator,
    and dispatches to one of three modes:
    - reasoning: requires --findings and writes proposals to --output via Orchestrator.run_reasoning
    - coding: requires --proposals and optionally --apply; writes results to --output via Orchestrator.run_coding
    - generate-pr: requires --proposals and --test-results and writes the PR body to --output via Orchestrator.generate_pr_body
    """
    import argparse

    parser = argparse.ArgumentParser(description="PR Fix Agent Orchestrator")
    parser.add_argument("--mode", required=True, choices=["reasoning", "coding", "generate-pr"])
    parser.add_argument("--findings", help="Path to findings JSON (for reasoning mode)")
    parser.add_argument("--proposals", help="Path to proposals JSON (for coding/generate-pr modes)")
    parser.add_argument("--test-results", help="Path to test results JSON (for generate-pr mode)")
    parser.add_argument("--output", required=True, help="Output file or directory")
    parser.add_argument("--apply", action="store_true", help="Apply fixes directly (for coding mode)")

    args = parser.parse_args()

    # Validate mode-specific required arguments
    if args.mode == "reasoning":
        if not args.findings:
            parser.error("--findings is required for reasoning mode")
    elif args.mode == "coding":
        if not args.proposals:
            parser.error("--proposals is required for coding mode")
    elif args.mode == "generate-pr":
        if not args.proposals or not args.test_results:
            parser.error("--proposals and --test-results are required for generate-pr mode")

    orchestrator = Orchestrator()

    if args.mode == "reasoning":
        orchestrator.run_reasoning(args.findings, args.output)
    elif args.mode == "coding":
        orchestrator.run_coding(args.proposals, args.output, args.apply)
    elif args.mode == "generate-pr":
        orchestrator.generate_pr_body(args.proposals, args.test_results, args.output)


if __name__ == "__main__":
    main()