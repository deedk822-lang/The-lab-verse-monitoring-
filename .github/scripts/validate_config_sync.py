import ast
import json
import sys

def extract_python_env_vars(file_path):
    """Scans Python files for os.getenv() calls."""
    env_vars = set()
    try:
        with open(file_path, 'r') as f:
            tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Attribute):
                        if node.func.attr == 'getenv' and isinstance(node.func.value, ast.Attribute):
                             # Matches os.getenv
                            if node.args and isinstance(node.args[0], ast.Constant):
                                env_vars.add(node.args[0].value)
    except Exception:
        pass
    return env_vars

def extract_vercel_env_vars(file_path):
    """Scans vercel.json for env keys."""
    try:
        with open(file_path, 'r') as f:
            config = json.load(f)
            # Correctly parse the top-level 'env' block
            env_vars = set(config.get('env', {}).keys())
            return env_vars
    except Exception:
        return set()

def main():
    python_vars = extract_python_env_vars('talent_scout.py')
    vercel_vars = extract_vercel_env_vars('vercel.json')

    print(f"Python Requires: {python_vars}")
    print(f"Vercel Provides: {vercel_vars}")

    drift = False

    # Check for missing in Vercel
    missing_in_vercel = python_vars - vercel_vars
    if missing_in_vercel:
        print(f"\n[CRITICAL] Configuration Drift: Missing in Vercel: {missing_in_vercel}")
        drift = True

    # Check for Ghost Variables in Vercel
    ghost_vars = vercel_vars - python_vars
    if ghost_vars:
        print(f"\n[WARNING] Ghost Variables in Vercel (Not used in code): {ghost_vars}")
        # In this specific migration, Ghost Vars (like Airtable) are BLOCKERS
        if "AIRTABLE" in str(ghost_vars):
             print("[CRITICAL] Legacy Airtable variables must be removed.")
             drift = True

    if drift:
        sys.exit(1)
    else:
        print("\n[SUCCESS] Configuration Synchronized.")

if __name__ == "__main__":
    main()
