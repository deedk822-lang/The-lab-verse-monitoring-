import os
import sys
import json
import re
from typing import Set

def extract_env_vars_from_code(file_path: str) -> Set[str]:
    """Extracts environment variable names from os.getenv() calls in a Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code_content = f.read()
    except FileNotFoundError:
        print(f"❌ Error: File {file_path} not found.")
        return set()

    # Regex pattern to find os.getenv('VAR_NAME'), os.environ.get('VAR_NAME'), os.environ['VAR_NAME']
    # This pattern captures the variable name inside the quotes/apostrophes.
    # It assumes simple string literals, which is the common case.
    pattern = r"os\.(?:getenv|environ(?:\.get|\[))\s*['\"]([A-Z_][A-Z0-9_]*)['\"].*?\)?"
    matches = re.findall(pattern, code_content)
    return set(matches)

def extract_env_vars_from_vercel_config(config_path: str) -> Set[str]:
    """Extracts environment variable names from vercel.json (top-level 'env' object)."""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: File {config_path} not found.")
        return set()
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in {config_path}: {e}")
        return set()

    # vercel.json typically has env vars at the top level under the 'env' key
    # or potentially under build.env or dev.env, but top-level is most common for runtime vars
    env_block = config.get('env', {})
    # vercel.json env block can have values as strings or objects like {"source": "shell", "value": "..."}
    # We only care about the keys (variable names)
    return set(env_block.keys())

def check_sync():
    """Main function to perform the sync check."""
    print("🔍 Audit: Scanning for 'Ghost Variables' and 'Zombie Variables'...")

    # Load variables from both sources
    code_vars = extract_env_vars_from_code('talent_scout.py')
    infra_vars = extract_env_vars_from_vercel_config('vercel.json')

    # Define variables that might exist in config but are not explicitly used in code (e.g., Node.js defaults)
    # These are typically provided by the platform or runtime and might not be explicitly fetched in Python.
    # Adjust this set based on your specific runtime environment if necessary.
    ignored_vars = {'NODE_ENV', 'VERCEL', 'VERCEL_URL', 'VERCEL_ENV'}

    # Calculate drift
    ghost_vars = infra_vars - code_vars - ignored_vars
    zombie_vars = code_vars - infra_vars

    drift_detected = False

    # Report Ghost Variables (In Infra, not in Code) - Warning
    if ghost_vars:
        print(f"⚠️  WARNING: Ghost Variables found in vercel.json (defined but not used in talent_scout.py): {ghost_vars}")
        print("   -> Consider removing them from vercel.json if they are truly unused.")

    # Report Zombie Variables (In Code, not in Infra) - Critical Error
    if zombie_vars:
        print(f"❌ CRITICAL: Zombie Variables found in talent_scout.py but missing from vercel.json: {zombie_vars}")
        print("   -> Deployment will likely fail. These variables must be defined in vercel.json.")
        drift_detected = True

    if drift_detected:
        print("❌ Configuration drift detected. Please fix before committing.")
        return False
    else:
        print("✅ Sync Status: Code and Configuration are aligned.")
        return True

if __name__ == "__main__":
    success = check_sync()
    sys.exit(0 if success else 1)
