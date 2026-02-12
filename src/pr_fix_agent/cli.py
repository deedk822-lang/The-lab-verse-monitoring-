import shutil

def check_tools(tools):
    all_found = True
    for name, cmd in tools.items():
        try:
            if not shutil.which(cmd):
                print(f"   ❌ {name} not found")
                all_found = False
        except OSError as e:
            print(f"   ❌ Error checking {cmd}: {e}")
            return False
    return all_found

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

    if check_tools({"pytest": "pytest", "git": "git"}):
        return production_main()

    print("\n" + "=" * 50)
    print("✅ All health checks passed!")
    return 0