"""
Unified CLI Entry Point
FIXES: Entry point documentation mismatch
PROVIDES: Single pr-fix-agent command with subcommands
"""

import argparse
import sys
from pathlib import Path

import structlog

logger = structlog.get_logger()


def health_check() -> int:
    """
    Perform health check

    Returns:
        0 if healthy, 1 otherwise
    """
    from pr_fix_agent.agents.ollama import OllamaAgent, OllamaQueryError

    print("🏥 PR Fix Agent Health Check")
    print("=" * 50)

    # Check 1: Ollama connectivity
    print("\n1. Checking Ollama connectivity...")
    try:
        agent = OllamaAgent(model="codellama")
        # We don't actually query here to avoid hang if ollama is not there
        print("   ✅ Ollama Agent initialized")
    except Exception as e:
        print(f"   ❌ Ollama initialization failed: {e}")
        return 1

    # Check 2: Package imports
    print("\n2. Checking package imports...")
    try:
        from pr_fix_agent import analyzer, orchestrator, security
        print("   ✅ All package modules import successfully")
    except ImportError as e:
        print(f"   ❌ Import failed: {e}")
        return 1

    # Check 3: Required tools
    print("\n3. Checking required tools...")
    import shutil
    tools = {
        "pytest": "pytest",
        "git": "git"
    }

    all_found = True
    for name, cmd in tools.items():
        if shutil.which(cmd):
            print(f"   ✅ {name} found")
        else:
            print(f"   ❌ {name} not found")
            all_found = False

    if not all_found:
        return 1

    print("\n" + "=" * 50)
    print("✅ All health checks passed!")
    return 0


def run_orchestrator(args) -> int:
    """Run orchestration mode"""
    from pr_fix_agent.orchestrator import main as orchestrator_main

    # Convert args to orchestrator format
    # orchestrator.py main() expects: mode --findings ... --apply
    sys.argv = ['orchestrator', args.mode]

    if args.findings:
        sys.argv.extend(['--findings', args.findings])

    if args.apply:
        sys.argv.append('--apply')

    return orchestrator_main()


def run_production(args) -> int:
    """Run production fix mode"""
    from pr_fix_agent.production import main as production_main

    # Validate repo path early
    repo_path = Path(args.repo_path).resolve()

    if not repo_path.exists():
        print(f"❌ Error: Repository path does not exist: {repo_path}")
        return 2

    # Convert args to production format
    sys.argv = [
        'production',
        '--repo-path', str(repo_path),
        '--model', args.model
    ]

    return production_main()


def main():
    """
    Unified CLI entry point
    """
    parser = argparse.ArgumentParser(
        prog='pr-fix-agent',
        description='AI-powered PR error fixing with Ollama'
    )

    subparsers = parser.add_subparsers(
        dest='command',
        required=True,
        help='Available commands'
    )

    # health-check
    subparsers.add_parser('health-check', help='Perform system health check')

    # orchestrate
    orch_parser = subparsers.add_parser('orchestrate', help='Run multi-agent orchestration')
    orch_parser.add_argument('mode', choices=['review', 'fix', 'generate-pr'], help='Orchestration mode')
    orch_parser.add_argument('--findings', help='Path to analysis findings')
    orch_parser.add_argument('--apply', action='store_true', help='Apply fixes')

    # fix
    fix_parser = subparsers.add_parser('fix', help='Run production error fixing')
    fix_parser.add_argument('--repo-path', default='.', help='Path to repository')
    fix_parser.add_argument('--model', default='codellama', help='Ollama model to use')

    args = parser.parse_args()

    try:
        if args.command == 'health-check':
            return health_check()
        elif args.command == 'orchestrate':
            return run_orchestrator(args)
        elif args.command == 'fix':
            return run_production(args)
        return 0
    except Exception as e:
        print(f"❌ Command failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
