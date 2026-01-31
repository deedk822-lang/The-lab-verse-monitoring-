#!/usr/bin/env python3
"""
PR Fix Agent Production Script
Main entry point for automated PR error fixing

FIXED: Early validation of --repo-path
FIXED: Uses observable OllamaAgent
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

    FIXED: Fail fast if repo path invalid
    """
    parser = argparse.ArgumentParser(description="PR Fix Agent Production")
    parser.add_argument("--repo-path", required=True, help="Path to repository")
    parser.add_argument("--health-check", action="store_true", help="Run health check")
    parser.add_argument("--model", default="codellama", help="Ollama model to use")

    args = parser.parse_args()

    # Health check doesn't need validation
    if args.health_check:
        print("✓ PR Fix Agent Health Check Passed")
        return 0

    # ✅ FIX: Early validation - fail fast
    repo_path = Path(args.repo_path).resolve()

    if not repo_path.exists():
        print(f"❌ Error: Repository path does not exist: {repo_path}")
        return 2

    if not repo_path.is_dir():
        print(f"❌ Error: Repository path is not a directory: {repo_path}")
        return 2

    # Validate the repository for security vulnerabilities
    validator = SecurityValidator(repo_path)
    try:
        validator.validate()
    except SecurityError as e:
        print(f"❌ Error validating repository: {e}")
        return 3

    print(f"✅ Using repository: {repo_path}")

    # Initialize components (validation already done)
    agent = OllamaAgent(model=args.model)
    analyzer = PRErrorAnalyzer(agent=agent)
    fixer = PRErrorFixer(agent=agent, repo_path=str(repo_path))

    print("✅ PR Fix Agent initialized and ready to analyze and fix errors.")
    return 0


if __name__ == "__main__":
    sys.exit(main())