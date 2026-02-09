
import os
import yaml
import sys
import re
import ast
import textwrap

def validate_embedded_python(code):
    # Replace GHA expressions with 'None' to avoid SyntaxError
    # We use a non-greedy match to stay within one expression
    clean_code = re.sub(r'\${{.*?}}', 'None', code)
    try:
        ast.parse(clean_code)
        return True, None
    except SyntaxError as e:
        return False, str(e)

def check_workflow(filepath):
    errors = []
    try:
        with open(filepath, 'r') as f:
            content = f.read()

        # 1. Global ternary check in GHA expressions (raw content)
        # Matches ${{ condition ? 'a' : 'b' }}
        ternary_matches = re.findall(r'\${{\s*[^}]*?\?[^}]*?:[^}]*?}}', content)
        for match in ternary_matches:
            errors.append(f"Unsupported ternary operator in GHA expression: {match}")

        # 2. YAML parsing and per-step checks
        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError as e:
            return [f"YAML Error: {e}"]

        if data and 'jobs' in data:
            for job_name, job in data['jobs'].items():
                if not isinstance(job, dict): continue
                steps = job.get('steps', [])
                if not isinstance(steps, list): continue
                for step in steps:
                    if not isinstance(step, dict): continue
                    run = step.get('run', '')
                    if not isinstance(run, str): continue

                    # Check for python3 -c usage
                    if 'python3 -c' in run:
                        # Find the python code inside quotes
                        # Handles both " and ' but doesn't handle escaped quotes within well
                        py_c_matches = re.finditer(r'python3\s+-c\s+([\'"])(.*?)\1', run, re.DOTALL)
                        for match in py_c_matches:
                            py_code = match.group(2)
                            if '\n' in py_code:
                                if 'textwrap.dedent' not in run:
                                    # Check for indentation in py_code
                                    lines = py_code.split('\n')
                                    # If first line is empty (common), skip it
                                    check_lines = lines[1:] if not lines[0].strip() else lines
                                    if any(line.startswith(' ') or line.startswith('\t') for line in check_lines if line.strip()):
                                        errors.append(f"Step '{step.get('name', 'unnamed')}' in job '{job_name}' has indented multi-line python3 -c without textwrap.dedent.")

                                # Validate syntax
                                test_code = py_code
                                if 'textwrap.dedent' in run:
                                    # Attempt to extract what's inside dedent('''...''')
                                    dedent_match = re.search(r"textwrap\.dedent\(\s*['\"]{3}(.*?)['\"]{3}\s*\)", run, re.DOTALL)
                                    if dedent_match:
                                        test_code = textwrap.dedent(dedent_match.group(1))

                                ok, err = validate_embedded_python(test_code)
                                if not ok:
                                    # If it failed due to indentation, it confirms the issue
                                    errors.append(f"Python syntax error in step '{step.get('name', 'unnamed')}': {err}")

    except Exception as e:
        errors.append(f"Validator error: {e}")

    return errors

def main():
    workflows_dir = '.github/workflows'
    if not os.path.isdir(workflows_dir):
        print(f"Directory not found: {workflows_dir}")
        sys.exit(1)

    files = [f for f in os.listdir(workflows_dir) if f.endswith('.yml') or f.endswith('.yaml') or f.endswith('.disabled')]
    all_ok = True
    print(f"Validating {len(files)} workflow files...\n")

    for f in sorted(files):
        path = os.path.join(workflows_dir, f)
        errors = check_workflow(path)
        if errors:
            print(f"❌ {f}:")
            for err in errors:
                print(f"  - {err}")
            all_ok = False
        else:
            print(f"✅ {f}")

    if not all_ok:
        print("\nValidation failed!")
        sys.exit(1)
    else:
        print("\nAll workflow files are valid.")

if __name__ == "__main__":
    main()
