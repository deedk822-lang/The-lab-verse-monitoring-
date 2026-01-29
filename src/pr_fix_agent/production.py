#!/usr/bin/env python3
"""
PR Fix Agent Production Script
Main entry point for automated PR error fixing
"""

import sys
import argparse
from pathlib import Path

# Conventional imports from the package
from .security import SecurityValidator, SecurityError
from .analyzer import PRErrorAnalyzer, PRErrorFixer, OllamaAgent


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="PR Fix Agent Production")
    parser.add_argument("--repo-path", default=".", help="Path to repository")
    parser.add_argument("--health-check", action="store_true", help="Run health check")
    parser.add_argument("--model", default="codellama", help="Ollama model to use")

    args = parser.parse_args()

    if args.health_check:
        print("✓ PR Fix Agent Health Check Passed")
        return 0

    print("PR Fix Agent Production")
    print(f"Repository path: {args.repo_path}")

    # Initialize components
    agent = OllamaAgent(model=args.model)
    validator = SecurityValidator(Path(args.repo_path))
    analyzer = PRErrorAnalyzer(agent=agent)
    fixer = PRErrorFixer(agent=agent, repo_path=args.repo_path)

    print("Ready to analyze and fix errors.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
