import json
import sys
import astroid

def extract_python_env_vars_astroid(file_path: str) -> set:
    """
    Uses astroid to find environment variable names from calls like:
    - os.getenv('VAR_NAME')
    - from os import getenv; getenv('VAR_NAME')
    - import os as alias; alias.getenv('VAR_NAME')
    """
    env_vars = set()
    try:
        module = astroid.MANAGER.ast_from_file(file_path)

        for node in module.nodes_of_class(astroid.Call):
            func = node.func

            # Helper to add variable from argument
            def add_arg(call_node):
                if call_node.args:
                    first_arg = call_node.args[0]
                    # Infer the value to ensure we get the literal string if possible
                    try:
                        # Infer returns a generator, take the first result
                        inferred_val = next(first_arg.infer())
                        if isinstance(inferred_val, astroid.Const):
                            if isinstance(inferred_val.value, str):
                                env_vars.add(inferred_val.value)
                    except (StopIteration, astroid.InferenceError):
                        # Fallback: If inference fails, try to check the AST directly for a constant
                        if isinstance(first_arg, astroid.Const) and isinstance(first_arg.value, str):
                            env_vars.add(first_arg.value)

            # Case 1: os.getenv(...) or alias.getenv(...)
            if isinstance(func, astroid.Attribute):
                # Try to infer what 'os' or 'alias' refers to
                try:
                    # func.expr is the object (e.g., Name(id='os'))
                    for inferred_obj in func.expr.infer():
                        # Check if the inferred object is the 'os' module
                        if isinstance(inferred_obj, astroid.Module) and inferred_obj.name == 'os':
                            # Check if the attribute name is 'getenv'
                            if func.attrname == 'getenv':
                                add_arg(node)
                                break
                except astroid.InferenceError:
                    pass

            # Case 2: getenv(...) imported from os
            elif isinstance(func, astroid.Name):
                # Look up the definition of this name in the current scope
                # module.locals gives a list of assignment/import nodes for that name
                defs = module.locals.get(func.name, [])
                for def_node in defs:
                    # Check if it was imported from 'os'
                    if isinstance(def_node, astroid.ImportFrom) and def_node.modname == 'os':
                        # def_node.names is a list of tuples (name, asname)
                        # We need to find if 'getenv' was imported
                        for imported_name, imported_as in def_node.names:
                            # Matches 'import getenv' or 'import getenv as get'
                            if imported_name == 'getenv' and (imported_as is None or imported_as == func.name):
                                add_arg(node)
                                break

    except FileNotFoundError:
        print(f"❌ Error: File {file_path} not found.", file=sys.stderr)
        sys.exit(1)
    except (astroid.AstroidBuildingError, SyntaxError) as e:
        print(f"Warning: Could not parse Python file {file_path}: {e}", file=sys.stderr)

    return env_vars


def extract_vercel_env_vars(file_path: str) -> set:
    """
    Scans vercel.json for env keys.
    Handles both:
    1. Top-level 'env' object: { "env": { "VAR": "val" } }
    2. Build env array: { "build": { "env": [ { "key": "VAR" } ] } }
    """
    try:
        with open(file_path, encoding='utf-8') as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Warning: Could not parse vercel.json file {file_path}: {e}", file=sys.stderr)
        return set()

    env_vars = set()

    # Case 1: Check build.env (Array of objects) - Common Vercel Pattern
    build_env = config.get('build', {}).get('env', [])
    if isinstance(build_env, list):
        for item in build_env:
            if isinstance(item, dict) and 'key' in item:
                env_vars.add(item['key'])
    elif isinstance(build_env, dict):
        # Some configs use dict in build.env
        env_vars.update(build_env.keys())

    # Case 2: Check top-level env (Dict)
    top_env = config.get('env', {})
    if isinstance(top_env, dict):
        env_vars.update(top_env.keys())

    return env_vars


import argparse

def main():
    parser = argparse.ArgumentParser(description="Validate config-code sync.")
    parser.add_argument("--py-file", default="talent_scout.py", help="Python file to scan.")
    parser.add_argument("--vercel-file", default="vercel.json", help="Vercel config file.")
    args = parser.parse_args()

    python_file = args.py_file
    vercel_file = args.vercel_file

    print(f"🔍 Scanning {python_file} (Semantic Analysis via Astroid)...")
    python_vars = extract_python_env_vars_astroid(python_file)
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
        if any("AIRTABLE" in var for var in ghost_vars):
            print("   -> CRITICAL: Legacy Airtable variables must be removed.")
            drift_detected = True

    if drift_detected:
        print("\n💥 Configuration drift detected. Fix required.")
        sys.exit(1)
    else:
        print("\n✅ Configuration Synchronized: System Integrity Verified.")
        sys.exit(0)

if __name__ == "__main__":
    main()
