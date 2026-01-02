import json
import sys
import os
import subprocess # For git diff
from typing import Set, List
import logging
import astroid
# Import the modern builder
from astroid.builder import AstroidBuilder # Modern import
from astroid import nodes
from astroid.exceptions import AstroidError, InferenceError

# Configure logging for the script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_changed_py_files() -> List[str]:
    """
    Gets a list of Python files that were added or modified in the current diff
    relative to the base branch of the PR.
    Falls back to scanning all files if git history is insufficient or not in PR context.
    """
    try:
        # Get the base branch name from the environment (set by GitHub Actions)
        base_ref = os.getenv('GITHUB_BASE_REF')
        if base_ref:
             # Get the merge base between the base branch and HEAD
             merge_base_cmd = ["git", "merge-base", f"origin/{base_ref}", "HEAD"]
             merge_base_result = subprocess.run(merge_base_cmd, capture_output=True, text=True)
             if merge_base_result.returncode == 0:
                 merge_base_sha = merge_base_result.stdout.strip()
                 # Diff between merge base and HEAD to get changes in the PR
                 diff_cmd = ["git", "diff", "--name-only", "--diff-filter=AM", merge_base_sha, "HEAD"]
                 result = subprocess.run(diff_cmd, capture_output=True, text=True, check=True)
                 changed_files = result.stdout.strip().split('\n')
                 return [f for f in changed_files if f and f.endswith('.py')]
             else:
                 logger.warning(f"Could not find merge base with {base_ref}. Scanning all files.")
        else:
             logger.warning("GITHUB_BASE_REF not set (not a PR context?). Scanning all files.")

        # Fallback: scan all files if git diff fails or base ref is unknown
        return []
    except subprocess.CalledProcessError as e:
        logger.warning(f"Could not get git diff: {e}. Scanning all files.")
        return []
    except Exception as e:
        logger.warning(f"Unexpected error getting git diff: {e}. Scanning all files.")
        return []

def get_inferred_env_vars_astroid(file_path: str) -> Set[str]:
    """
    Uses astroid.AstroidBuilder for semantic matching.
    Matches: os.getenv('VAR_NAME'), os.environ.get('VAR_NAME'), and aliased imports resolving to these.
    """
    env_vars = set()
    try:
        # Use the modern AstroidBuilder
        module = astroid.MANAGER.ast_from_file(file_path)

        for call_node in module.nodes_of_class(nodes.Call):
            try:
                # Use infer() to determine function being called
                for inferred in call_node.func.infer():
                    # Check for the qualified name (qname)
                    if (hasattr(inferred, 'qname') and
                        inferred.qname() in ['os.getenv', 'os.environ.get']):
                        # Extract first argument (the env var name)
                        if call_node.args and hasattr(call_node.args[0], 'value'):
                            var_name = call_node.args[0].value
                            if isinstance(var_name, str):
                                env_vars.add(var_name)
            except (InferenceError, StopIteration, AttributeError):
                # Inference can fail for complex expressions, skip safely
                continue
            except Exception as e:
                logger.warning(f"Error processing node in {file_path}: {e}")
                continue

    except FileNotFoundError:
        logger.error(f"File {file_path} not found.")
    except AstroidError as e:
        logger.error(f"Astroid parsing failed for {file_path}: {e}")
    except Exception as e:
        logger.error(f"Error analyzing {file_path}: {e}")

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
                    logger.warning(f"'env' block is neither dict nor list (found {type(env_block).__name__}). Skipping.")
                return set()

        # Check top-level env
        top_env = config.get('env')
        vars_set.update(extract_from_env_block(top_env))

        # Check build.env
        build_env = config.get('build', {}).get('env')
        vars_set.update(extract_from_env_block(build_env))

        return vars_set

    except FileNotFoundError:
        logger.error(f"File {file_path} not found.")
        return set() # Return empty set if vercel.json doesn't exist, potentially allow-listing is fine
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        sys.exit(1) # Exit on invalid JSON
    except Exception as e:
        logger.error(f"Error parsing {file_path}: {e}")
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
                        logger.warning(f"Line {line_num} in {file_path} does not contain '=': '{line}'")
    except FileNotFoundError:
        logger.info(f"File {file_path} not found. Skipping.")
        # This is okay, .env.example is optional
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        # Depending on requirements, might exit here, but often it's just a warning
        # sys.exit(1)

    return vars_set


def main():
    # Determine files to scan: changed files first, fallback to all
    changed_py_files = get_changed_py_files()
    if changed_py_files:
        logger.info(f"Scanning changed Python files: {changed_py_files}")
        files_to_scan = changed_py_files
    else:
        logger.info("No changed Python files found or git diff failed. Scanning all Python files...")
        files_to_scan = []
        for root, dirs, files in os.walk("."):
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.venv', 'venv', 'node_modules']]
            for file in files:
                if file.endswith(".py"):
                    files_to_scan.append(os.path.join(root, file))

    all_code_vars = set()
    for py_file_path in files_to_scan:
        logger.info(f"Scanning {py_file_path} for env vars...")
        file_vars = get_inferred_env_vars_astroid(py_file_path) # Use the updated function
        all_code_vars.update(file_vars)
        logger.info(f"   Found: {sorted(file_vars)}")

    logger.info(f"Scanning vercel.json for environment variables...")
    vercel_vars = load_vercel_secrets('vercel.json')
    logger.info(f"   Found: {sorted(vercel_vars)}")

    logger.info(f"Scanning .env.example for example environment variables...")
    example_vars = load_example_env_vars('.env.example')
    logger.info(f"   Found: {sorted(example_vars)}")

    # Combine infrastructure-defined variables (Vercel + Example env)
    infra_vars = vercel_vars | example_vars

    # Analysis
    missing_in_infra = all_code_vars - infra_vars
    ghost_vars_in_infra = infra_vars - all_code_vars

    drift_detected = False

    if missing_in_infra:
        logger.error(f"CRITICAL: Code uses variables missing from Vercel/Example config: {sorted(missing_in_infra)}")
        logger.error("   -> Deployment will likely fail. These variables must be defined in vercel.json or .env.example.")
        drift_detected = True

    if ghost_vars_in_infra:
        logger.warning(f"WARNING: Variables defined in Vercel/Example config but unused in code: {sorted(ghost_vars_in_infra)}")
        # Check for legacy/deprecated services
        legacy_found = [var for var in ghost_vars_in_infra if 'AIRTABLE' in var.upper() or 'PROXYCURL' in var.upper()]
        if legacy_found:
            logger.error(f"CRITICAL: Legacy Airtable/Proxycurl variables detected: {legacy_found}")
            logger.error("   -> These must be removed from vercel.json/.env.example.")
            drift_detected = True

    if drift_detected:
        logger.error("Configuration drift detected. Please fix before committing/merging.")
        sys.exit(1)
    else:
        logger.info("Configuration Synchronized: Code, Vercel config, and .env.example align.")
        sys.exit(0)

if __name__ == "__main__":
    main()
