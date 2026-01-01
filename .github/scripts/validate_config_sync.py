import json
import sys
import astroid # Import astroid

def get_inferred_env_vars(file_path):
    """Uses astroid to find all calls that semantically resolve to os.getenv."""
    env_vars = set()
    try:
        with open(file_path, "r") as f:
            tree = astroid.parse(f.read())

        for call in tree.nodes_of_class(astroid.Call):
            try:
                # Ask astroid what this function call actually is
                inferred = call.func.infer()
                for val in inferred:
                    # Check for os.getenv, os.environ.get, etc.
                    if val.qname() in ['os.getenv', 'os.environ.get', 'os.environ.__getitem__']:
                        if call.args and isinstance(call.args[0], astroid.Const):
                            env_vars.add(call.args[0].value)
            except astroid.InferenceError:
                continue
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
    return env_vars


def extract_vercel_env_vars(file_path: str) -> set:
    """
    Scans vercel.json for env keys at the top level 'env' object.
    This matches the standard Vercel configuration structure.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: File {file_path} not found.", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in {file_path}: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error parsing {file_path}: {e}", file=sys.stderr)
        sys.exit(1)

    # vercel.json typically has env vars at the top level under the 'env' key as an object
    # e.g., { "env": { "VAR_NAME": "value", ... } }
    env_block = config.get('env', {})
    if not isinstance(env_block, dict):
        print(f"⚠️ Warning: 'env' in {file_path} is not an object (found {type(env_block).__name__}). Skipping.", file=sys.stderr)
        return set()
    # Return the keys (variable names) from the env object
    return set(env_block.keys())

def main():
    python_file = 'talent_scout.py'
    vercel_file = 'vercel.json'

    print(f"🔍 Scanning {python_file} (Semantic Analysis via Astroid)...")
    python_vars = get_inferred_env_vars(python_file)
    print(f"   Found in code: {python_vars}")

    print(f"🔍 Scanning {vercel_file} (Structural Analysis)...")
    vercel_vars = extract_vercel_env_vars(vercel_file)
    print(f"   Found in config: {vercel_vars}")

    drift_detected = False

    # 1. Missing in Vercel (Critical Drift)
    missing_in_vercel = python_vars - vercel_vars
    if missing_in_vercel:
        print(f"\n❌ CRITICAL: Variables used in code are missing from config: {missing_in_vercel}")
        drift_detected = True

    # 2. Ghost Variables (Legacy)
    ghost_vars = vercel_vars - python_vars
    if ghost_vars:
        print(f"\n⚠️ WARNING: Ghost variables in config: {ghost_vars}")
        legacy_found = [var for var in ghost_vars if 'AIRTABLE' in var or 'PROXYCURL' in var]
        if legacy_found:
            print(f"   -> CRITICAL: Legacy variables detected: {legacy_found}")
            drift_detected = True

    if drift_detected:
        print("\n💥 Configuration drift detected. Please fix before committing.")
        sys.exit(1)
    else:
        print("\n✅ Configuration Synchronized: Code and Vercel config align.")
        sys.exit(0)

if __name__ == "__main__":
    main()
