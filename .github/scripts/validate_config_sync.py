import json
import sys
import os
import astroid # Import astroid
from typing import Set

def get_inferred_env_vars_astroid(file_path: str) -> Set[str]:
    """
    Uses astroid.qname() for semantic matching.
    Matches: os.getenv('VAR_NAME'), os.environ.get('VAR_NAME'), and aliased imports resolving to these.
    """
    env_vars = set()
    try:
        module = astroid.MANAGER.ast_from_file(file_path)
        for call_node in module.nodes_of_class(astroid.Call):
            try:
                # Infer the function being called
                inferred_func = next(call_node.func.infer())

                # Check the Qualified Name (qname)
                qname = inferred_func.qname()

                # Check for the specific functions we are interested in
                if qname in ['os.getenv', 'os.environ.get']:
                    if call_node.args:
                        first_arg = call_node.args[0]
                        # Check if the argument is a constant string
                        if isinstance(first_arg, astroid.Const):
                            if isinstance(first_arg.value, str):
                                env_vars.add(first_arg.value)
            except (StopIteration, astroid.InferenceError, AttributeError):
                # Inference failed or node structure unexpected, skip safely
                continue
            except Exception as e:
                # Catch any other unexpected errors during node processing
                print(f"⚠️ Warning: Error processing node in {file_path}: {e}", file=sys.stderr)
                continue

    except FileNotFoundError:
        print(f"❌ Error: File {file_path} not found.", file=sys.stderr)
        # For this script's purpose, warn and continue scanning other files.
    except Exception as e:
        print(f"❌ Error analyzing {file_path}: {e}", file=sys.stderr)

    return env_vars

def load_vercel_secrets(file_path: str) -> Set[str]:
    """
    Loads environment variables from vercel.json.
    Handles both object { "VAR": "value" } and array [ { "key": "VAR", "value": "..." } ] structures.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        vars_set = set()

        def extract_from_env_block(env_block):
            if isinstance(env_block, dict):
                return set(env_block.keys())
            elif isinstance(env_block, list):
                return {item.get('key') for item in env_block if isinstance(item, dict) and 'key' in item}
            else:
                if env_block is not None:
                    print(f"⚠️ Warning: 'env' block is neither dict nor list (found {type(env_block).__name__}). Skipping.", file=sys.stderr)
                return set()

        # Check top-level env
        top_env = config.get('env')
        vars_set.update(extract_from_env_block(top_env))

        # Check build.env
        build_env = config.get('build', {}).get('env')
        vars_set.update(extract_from_env_block(build_env))

        return vars_set

    except FileNotFoundError:
        print(f"❌ Error: File {file_path} not found.", file=sys.stderr)
        return set() # Return empty set if vercel.json doesn't exist, potentially allow-listing is fine
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in {file_path}: {e}", file=sys.stderr)
        sys.exit(1) # Exit on invalid JSON
    except Exception as e:
        print(f"❌ Error parsing {file_path}: {e}", file=sys.stderr)
        sys.exit(1)

def load_example_env_vars(file_path: str) -> Set[str]:
    """
    Loads variable names (without values) from a .env.example file.
    Format: VAR_NAME=optional_default_value
    """
    vars_set = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, start=1):
                line = line.strip()
                if line and not line.startswith('#'): # Ignore empty lines and comments
                    # Split on the first '=' to get key and value
                    if '=' in line:
                        key = line.split('=', 1)[0].strip()
                        if key:
                            vars_set.add(key)
                    else:
                        print(f"⚠️ Warning: Line {line_num} in {file_path} does not contain '=': '{line}'")
    except FileNotFoundError:
        print(f"ℹ️ Info: File {file_path} not found. Skipping.", file=sys.stderr)
        # This is okay, .env.example is optional
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}", file=sys.stderr)
        # Depending on requirements, might exit here, but often it's just a warning
        # sys.exit(1)

    return vars_set


def main():
    # SCOPING: Scan all Python files in the repository
    all_code_vars = set()
    for root, dirs, files in os.walk("."):
        # Exclude common directories like .git, __pycache__, etc.
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.venv', 'venv', 'node_modules']]
        for file in files:
            if file.endswith(".py"):
                py_file_path = os.path.join(root, file)
                print(f"🔍 Scanning {py_file_path} for env vars...")
                file_vars = get_inferred_env_vars_astroid(py_file_path)
                all_code_vars.update(file_vars)
                print(f"   Found: {sorted(file_vars)}")

    print(f"🔍 Scanning vercel.json for environment variables...")
    vercel_vars = load_vercel_secrets('vercel.json')
    print(f"   Found: {sorted(vercel_vars)}")

    print(f"🔍 Scanning .env.example for example environment variables...")
    example_vars = load_example_env_vars('.env.example')
    print(f"   Found: {sorted(example_vars)}")

    # Combine infrastructure-defined variables (Vercel + Example env)
    infra_vars = vercel_vars | example_vars

    # Analysis
    missing_in_infra = all_code_vars - infra_vars
    ghost_vars_in_infra = infra_vars - all_code_vars

    drift_detected = False

    if missing_in_infra:
        print(f"\n❌ CRITICAL: Code uses variables missing from Vercel/Example config: {sorted(missing_in_infra)}")
        print("   -> Deployment will likely fail. These variables must be defined in vercel.json or .env.example.")
        drift_detected = True

    if ghost_vars_in_infra:
        print(f"\n⚠️ WARNING: Variables defined in Vercel/Example config but unused in code: {sorted(ghost_vars_in_infra)}")
        # Check for legacy/deprecated services
        legacy_found = [var for var in ghost_vars_in_infra if 'AIRTABLE' in var.upper() or 'PROXYCURL' in var.upper()]
        if legacy_found:
            print(f"   -> CRITICAL: Legacy Airtable/Proxycurl variables detected: {legacy_found}")
            print("   -> These must be removed from vercel.json/.env.example.")
            drift_detected = True

    if drift_detected:
        print("\n💥 Configuration drift detected. Please fix before committing/merging.")
        sys.exit(1)
    else:
        print("\n✅ Configuration Synchronized: Code, Vercel config, and .env.example align.")
        sys.exit(0)

if __name__ == "__main__":
    main()
