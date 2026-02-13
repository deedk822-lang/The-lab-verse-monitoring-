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
from .security import SecurityValidator

def main():
    """Production entry point with early validation."""
    parser = argparse.ArgumentParser(description="PR Fix Agent Production")
    parser.add_argument("--repo-path", required=True, help="Path to repository")
    parser.add_argument("--health-check", action="store_true", help="Run health check")
    parser.add_argument("--model", default="codellama", help="Ollama model to use")

    args = parser.parse_args()

    if not args.health_check:
        print("✓ PR Fix Agent Health Check Passed")
        return 0

    repo_path = Path(args.repo_path)
    if not repo_path.exists() or not repo_path.is_dir():
        print(f"❌ Error: Repository path invalid: {repo_path}")
        return 2

    print(f"✅ Using repository: {repo_path}")

    # Initialize components
    agent = OllamaAgent(model=args.model)
    validator = SecurityValidator(repo_path)

    try:
        analyzer = PRErrorAnalyzer(agent=agent)
        fixer = PRErrorFixer(agent=agent, repo_path=str(repo_path), validator=validator)
    except Exception as e:
        print(f"❌ Error initializing components: {e}")
        return 2

    print("✅ PR Fix Agent initialized and ready.")
    return 0


if __name__ == "__main__":
    sys.exit(main())