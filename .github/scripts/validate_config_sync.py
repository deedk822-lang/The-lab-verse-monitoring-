import json
import sys
import astroid # Import astroid

def extract_python_env_vars_astroid(file_path: str) -> set:
    """
    Uses astroid to find environment variable names from calls like:
    - os.getenv('VAR_NAME')
    - from os import getenv; getenv('VAR_NAME')
    - import os as alias; alias.getenv('VAR_NAME')
    """
    env_vars = set()
    try:
        # Parse the file using astroid
        module = astroid.parse_file(file_path)

        # Walk the astroid tree looking for Call nodes
        for node in module.nodes_of_class(astroid.Call):
            func = node.func

            # Case 1: os.getenv(...) or alias.getenv(...) (Attribute access)
            if isinstance(func, astroid.Attribute):
                try:
                    # Infer the value part of the attribute (e.g., 'os' or 'alias')
                    for inferred_value in func.expr.infer():
                        # Check if the inferred value is the 'os' module
                        if (hasattr(inferred_value, 'name') and inferred_value.name == 'os'):
                             # Check if the attribute being accessed is 'getenv'
                             if func.attrname == 'getenv':
                                # Found os.getenv or alias.getenv where alias -> os
                                if node.args:
                                    first_arg = node.args[0]
                                    # Infer the value of the argument (the variable name)
                                    # This handles constants like 'VAR_NAME' or potentially simple expressions
                                    for inferred_arg in first_arg.infer():
                                        if (isinstance(inferred_arg, (astroid.Const, astroid.NameConstant)) and
                                            isinstance(inferred_arg.value, str)):
                                            env_vars.add(inferred_arg.value)
                                            break # Found a valid string constant, move to next arg/node
                                break # Found os.getenv call, move to next node

                except astroid.InferenceError:
                    # If inference fails for this specific node's function value, skip it
                    # This might happen if the value is a complex expression astroid cannot resolve
                    continue
                except (AttributeError, StopIteration):
                    # If attributes don't exist or infer() yields nothing unexpectedly, skip it
                    continue

            # Case 2: getenv(...) where getenv is imported from os (Name access)
            elif isinstance(func, astroid.Name):
                try:
                    # Look up the definition of this name in the current scope using astroid's lookup
                    # This finds where 'func.name' was defined (e.g., via 'from os import getenv')
                    stmts = module.locals.get(func.name, [])
                    for def_node in stmts:
                        # Check if the definition is an ImportFrom statement from 'os'
                        if isinstance(def_node, astroid.ImportFrom) and def_node.modname == 'os':
                             # Check if the imported name is specifically 'getenv'
                             imported_names = [name for name, alias in def_node.names]
                             if 'getenv' in imported_names:
                                 # Check the alias. If alias is None, func.name must be 'getenv'.
                                 # If alias is a string, func.name must match the alias.
                                 for name, alias in def_node.names:
                                     if name == 'getenv':
                                         if (alias is None and func.name == 'getenv') or (alias == func.name):
                                             # The name 'func.name' refers to 'os.getenv'
                                             # Now check the arguments
                                             if node.args:
                                                 first_arg = node.args[0]
                                                 for inferred_arg in first_arg.infer():
                                                     if (isinstance(inferred_arg, (astroid.Const, astroid.NameConstant)) and
                                                         isinstance(inferred_arg.value, str)):
                                                         env_vars.add(inferred_arg.value)
                                                         break # Found valid string constant, move to next arg/node
                                             break # Found the correct import match, move to next node
                except Exception:
                    # If lookup or processing fails for any reason, skip this node
                    # This is a broad catch, but lookup can involve complex logic
                    continue

    except FileNotFoundError:
        print(f"❌ Error: File {file_path} not found.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error parsing {file_path} with astroid: {e}", file=sys.stderr)
        sys.exit(1)

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

    print(f"🔍 Scanning {python_file} for environment variables using astroid...")
    python_vars = extract_python_env_vars_astroid(python_file)
    print(f"   Found in code: {sorted(python_vars)}") # Sort for easier reading

    print(f"🔍 Scanning {vercel_file} for environment variables...")
    vercel_vars = extract_vercel_env_vars(vercel_file)
    print(f"   Found in config: {sorted(vercel_vars)}") # Sort for easier reading

    drift_detected = False

    # 1. Check for missing in Vercel (Zombie Variables - Critical)
    missing_in_vercel = python_vars - vercel_vars
    if missing_in_vercel:
        print(f"\n❌ CRITICAL: Variables used in {python_file} are missing from {vercel_file}: {sorted(missing_in_vercel)}")
        print("   -> Deployment will likely fail. These variables must be defined in vercel.json.")
        drift_detected = True

    # 2. Check for Ghost Variables in Vercel (Warning, but check for legacy)
    ghost_vars = vercel_vars - python_vars
    if ghost_vars:
        print(f"\n⚠️ WARNING: Variables defined in {vercel_file} are not used in {python_file}: {sorted(ghost_vars)}")
        # Check for legacy Airtable or Proxycurl variables (Proxycurl is now known to be defunct)
        legacy_found = [var for var in ghost_vars if 'AIRTABLE' in var.upper() or 'PROXYCURL' in var.upper()] # Case-insensitive check
        if legacy_found:
            print(f"   -> CRITICAL: Legacy variables detected (Airtable/Proxycurl): {legacy_found}")
            print("   -> These must be removed from vercel.json.")
            drift_detected = True

    if drift_detected:
        print("\n💥 Configuration drift detected. Please fix before committing.")
        sys.exit(1)
    else:
        print("\n✅ Configuration Synchronized: Code and Vercel config align.")
        sys.exit(0)

if __name__ == "__main__":
    main()
