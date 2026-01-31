#!/usr/bin/env python3
"""
PR Fix Agent Production Script
Main entry point for automated PR error fixing
"""

import argparse
import sys
from pathlib import Path

from .analyzer import PRErrorAnalyzer, PRErrorFixer
from .ollama_agent import OllamaAgent
<<<<<<< HEAD
=======

# Conventional imports from the package
from .security import SecurityValidator
>>>>>>> main


def main():
    """Production entry point with early validation."""
    parser = argparse.ArgumentParser(description="PR Fix Agent Production")
    parser.add_argument("--repo-path", default=".", help="Path to repository")
    parser.add_argument("--health-check", action="store_true", help="Run health check")
    parser.add_argument("--model", default="codellama", help="Ollama model to use")

    args = parser.parse_args()

    if args.health_check:
        print("✓ PR Fix Agent Health Check Passed")
        return 0

    repo_path = Path(args.repo_path).resolve()
    if not repo_path.exists() or not repo_path.is_dir():
        print(f"❌ Error: Repository path invalid: {repo_path}")
        return 2

    print(f"✅ Using repository: {repo_path}")

    # Initialize components
    agent = OllamaAgent(model=args.model)
    validator = SecurityValidator(repo_path)
    analyzer = PRErrorAnalyzer(agent=agent)
    fixer = PRErrorFixer(agent=agent, repo_path=str(repo_path), validator=validator)

    print("✅ PR Fix Agent initialized and ready.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
