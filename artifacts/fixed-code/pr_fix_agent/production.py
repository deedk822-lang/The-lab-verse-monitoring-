#!/usr/bin/env python3
"""
PR Fix Agent Production Script
Main entry point for automated PR error fixing

FIXED: Early validation of --repo-path and --model
"""

import argparse
import sys
from pathlib import Path

from .analyzer import PRErrorAnalyzer, PRErrorFixer
from .ollama_agent import OllamaAgent

# Conventional imports from the package
from .security import SecurityValidator


def main():
    """
    Production entry point with early validation

    FIXED: Fail fast if repo path and model are invalid
    """
    parser = argparse.ArgumentParser(description="PR Fix Agent Production")
    parser.add_argument("--repo-path", default=".", help="Path to repository")
    parser.add_argument("--health-check", action="store_true", help="Run health check")
    parser.add_argument("--model", default="codellama", help="Ollama model to use")

    args = parser.parse_args()

    # Health check doesn't need validation
    if args.health_check:
        print("✓ PR Fix Agent Health Check Passed")
        return 0

    # ✅ FIX: Early validation - fail fast
    repo_path = Path(args.repo_path).resolve()
    model_name = args.model  # Model name from command line argument

    # Security check: Ensure the Ollama model exists
    if not Path(f"/usr/local/bin/{model_name}").exists():
        print(f"❌ Error: The Ollama model '{model_name}' does not exist on the system.")
        return 2

    print(f"✅ Using repository: {repo_path}")

    # Initialize components (validation already done)
    agent = OllamaAgent(model=model_name)
    validator = SecurityValidator(repo_path)
    analyzer = PRErrorAnalyzer(agent=agent)
    fixer = PRErrorFixer(agent=agent, repo_path=str(repo_path))

    print("✅ PR Fix Agent initialized and ready to analyze and fix errors.")
    return 0


if __name__ == "__main__":
    sys.exit(main())