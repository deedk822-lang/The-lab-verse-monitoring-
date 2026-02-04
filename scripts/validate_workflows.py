
import os
import yaml
import sys
import re
import ast
import textwrap

def validate_python_in_run(run_content, filename):
    """
    Attempts to validate Python code found in 'run' blocks.
    """
    errors = []

    # Pattern for python3 -c "..."
    # We look for both the old (buggy) and new (fixed) patterns
    c_blocks = re.findall(r"python3 -c \"([\s\S]*?)\"", run_content)
    for block in c_blocks:
        try:
            # If it uses the textwrap.dedent fix
            if "textwrap.dedent" in block:
                dedent_match = re.search(r"exec\(textwrap\.dedent\('''([\s\S]*)'''\)\)", block)
                if dedent_match:
                    py_code = textwrap.dedent(dedent_match.group(1))
                    ast.parse(py_code)
                else:
                    # Maybe it's not the exact pattern we expect but it uses textwrap
                    pass
            else:
                # Direct python code.
                # Note: ast.parse will fail if there's leading indentation that Python doesn't like.
                ast.parse(block)
        except SyntaxError as e:
            errors.append(f"Python Syntax Error in {filename}: {e}")

    return errors

def validate_gha_expressions(content, filename):
    """
    Checks for common GHA expression errors like ternary operators.
    """
    errors = []
    # Look for ${{ ... ? ... : ... }} which is not supported in GHA
    ternary_matches = re.findall(r"\$\{\{\s*[^}]*\?[^}]*:[^}]*\}\}", content)
    for match in ternary_matches:
        errors.append(f"GHA Expression Error in {filename}: Ternary operator '?' found in {match}. Use '&& ||' instead.")

    return errors

def validate_workflows():
    """
    Validates all YAML files in the .github/workflows directory.
    """
    workflows_dir = '.github/workflows'
    has_errors = False

    if not os.path.isdir(workflows_dir):
        print(f"Directory not found: {workflows_dir}")
        sys.exit(1)

    for filename in os.listdir(workflows_dir):
        if filename.endswith('.yml') or filename.endswith('.yaml'):
            filepath = os.path.join(workflows_dir, filename)
            try:
                with open(filepath, 'r') as f:
                    content = f.read()
                    data = yaml.safe_load(content)

                # Basic YAML is OK, now check deeper
                file_errors = []

                # Check GHA Expressions
                file_errors.extend(validate_gha_expressions(content, filename))

                # Check Python in run blocks
                if isinstance(data, dict) and 'jobs' in data:
                    for job_name, job in data['jobs'].items():
                        if 'steps' in job:
                            for step in job['steps']:
                                if 'run' in step:
                                    file_errors.extend(validate_python_in_run(step['run'], filename))

                if file_errors:
                    for err in file_errors:
                        print(f"❌ {err}")
                    has_errors = True
                else:
                    print(f"✅ {filename} - OK")

            except yaml.YAMLError as e:
                print(f"❌ {filename} - Error parsing YAML: {e}")
                has_errors = True
            except Exception as e:
                print(f"❌ {filename} - Unexpected error: {e}")
                has_errors = True

    if has_errors:
        sys.exit(1)
    else:
        print("\nAll workflow files passed validation (including Python & GHA expression checks).")

if __name__ == "__main__":
    validate_workflows()
