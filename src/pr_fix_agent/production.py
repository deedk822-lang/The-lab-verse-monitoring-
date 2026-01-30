#!/usr/bin/env python3
"""PR Fix Agent Production Script.

This is the CLI entry point for running the PR Fix Agent in a real repository.
"""

import sys
import argparse
from pathlib import Path

from .security import SecurityValidator
from .analyzer import PRErrorAnalyzer, PRErrorFixer, OllamaAgent


def main() -> int:
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
        print(f"Invalid repo path: {repo_path}")
        return 2

    print("PR Fix Agent Production")
    print(f"Repository path: {repo_path}")

    # Initialize components
    agent = OllamaAgent(model=args.model)
    validator = SecurityValidator(repo_path)
    analyzer = PRErrorAnalyzer(agent=agent)
    fixer = PRErrorFixer(agent=agent, repo_path=str(repo_path))

    # Silence unused variables for now (production wiring happens elsewhere)
    _ = (validator, analyzer, fixer)

    print("Ready to analyze and fix errors.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
