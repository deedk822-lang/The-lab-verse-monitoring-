"""
Unified CLI Entry Point
"""

import sys
import argparse
from pathlib import Path
import structlog

logger = structlog.get_logger()


def health_check() -> int:
    """
    Perform system health check

    Returns:
        0 if healthy, 1 otherwise
    """
    from pr_fix_agent.ollama_agent import OllamaAgent, OllamaQueryError

    print("🏥 PR Fix Agent Health Check")
    print("=" * 50)

    # Check 1: Ollama connectivity
    print("\n1. Checking Ollama connectivity...")
    try:
        agent = OllamaAgent(model="codellama")
        response = agent.query("test", timeout=10)
        print("   ✅ Ollama is running and responsive")
    except OllamaQueryError as e:
        print(f"   ❌ Ollama connectivity failed: {e}")
        print("   💡 Start Ollama with: ollama serve")
        return 1

    # Check 2: Package imports
    print("\n2. Checking package imports...")
    try:
        from pr_fix_agent import analyzer, security, orchestrator
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
    """Run multi-agent orchestration"""
    from pr_fix_agent.orchestrator import main as orchestrator_main

    # Convert args to orchestrator format
    sys.argv = [
        'orchestrator',
        '--mode', args.mode
    ]

    if args.findings:
        sys.argv.extend(['--findings', args.findings])

    if args.proposals:
        sys.argv.extend(['--proposals', args.proposals])

    if args.test_results:
        sys.argv.extend(['--test-results', args.test_results])

    if args.output:
        sys.argv.extend(['--output', args.output])

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

    if not repo_path.is_dir():
        print(f"❌ Error: Repository path is not a directory: {repo_path}")
        return 2

    print(f"✅ Using repository: {repo_path}")

    # Convert args to production format
    sys.argv = [
        'production',
        '--repo-path', str(repo_path),
        '--model', args.model
    ]

    if args.log_file:
        sys.argv.extend(['--log-file', args.log_file])

    return production_main()


def main():
    """
    Unified CLI entry point

    Usage:
        pr-fix-agent health-check
        pr-fix-agent orchestrate --mode reasoning --findings results/
        pr-fix-agent fix --repo-path /path/to/repo
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

    # ========================================================================
    # health-check command
    # ========================================================================

    health_parser = subparsers.add_parser(
        'health-check',
        help='Perform system health check'
    )

    # ========================================================================
    # orchestrate command
    # ========================================================================

    orch_parser = subparsers.add_parser(
        'orchestrate',
        help='Run multi-agent orchestration'
    )

    orch_parser.add_argument(
        '--mode',
        required=True,
        choices=['reasoning', 'coding', 'generate-pr'],
        help='Orchestration mode'
    )

    orch_parser.add_argument(
        '--findings',
        help='Path to analysis findings directory'
    )

    orch_parser.add_argument(
        '--proposals',
        help='Path to proposals JSON file'
    )

    orch_parser.add_argument(
        '--test-results',
        help='Path to test results JSON file'
    )

    orch_parser.add_argument(
        '--output',
        help='Output file path'
    )

    orch_parser.add_argument(
        '--apply',
        action='store_true',
        help='Apply fixes (for coding mode)'
    )

    # ========================================================================
    # fix command
    # ========================================================================

    fix_parser = subparsers.add_parser(
        'fix',
        help='Run production error fixing'
    )

    fix_parser.add_argument(
        '--repo-path',
        default='.',
        help='Path to repository (default: current directory)'
    )

    fix_parser.add_argument(
        '--model',
        default='codellama',
        help='Ollama model to use (default: codellama)'
    )

    fix_parser.add_argument(
        '--log-file',
        help='Path to CI/CD log file to analyze'
    )

    # ========================================================================
    # Parse and dispatch
    # ========================================================================

    args = parser.parse_args()

    logger.info(
        "cli_command_start",
        command=args.command
    )

    try:
        if args.command == 'health-check':
            return health_check()

        elif args.command == 'orchestrate':
            return run_orchestrator(args)

        elif args.command == 'fix':
            return run_production(args)

        else:
            print(f"❌ Unknown command: {args.command}")
            return 1

    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        return 130

    except Exception as e:
        logger.error(
            "cli_command_failed",
            command=args.command,
            error=str(e),
            exc_info=True
        )
        print(f"❌ Command failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())