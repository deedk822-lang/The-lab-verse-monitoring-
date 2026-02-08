
import os
import yaml
import sys
import re
import ast
import textwrap

def validate_workflows():
    """
    Validates all YAML files in the .github/workflows directory for both
    standard YAML syntax and common GitHub Actions expression/script errors.
    """
    workflows_dir = '.github/workflows'
    has_errors = False

    if not os.path.isdir(workflows_dir):
        print(f"Directory not found: {workflows_dir}")
        sys.exit(1)

    # Regex to find GHA expressions: ${{ ... }}
    gha_expr_pattern = re.compile(r'\$\{\{(.*?)\}\}')

    for filename in os.listdir(workflows_dir):
        if filename.endswith('.yml') or filename.endswith('.yaml') or filename.endswith('.yml.disabled') or filename.endswith('.yaml.disabled'):
            filepath = os.path.join(workflows_dir, filename)
            file_errors = []
            try:
                with open(filepath, 'r') as f:
                    content = f.read()
                    data = yaml.safe_load(content)

                # Check for ternary operators in GHA expressions
                expressions = gha_expr_pattern.findall(content)
                for expr in expressions:
                    if '?' in expr and ':' in expr:
                        # Defensive check: if it's inside quotes, it might be okay (though rare in GHA expr)
                        # But generally GHA doesn't support ternary at all.
                        file_errors.append(f"Potential unsupported ternary operator in expression: ${{{{{expr}}}}}")

                # Check for python3 -c blocks
                if data and isinstance(data, dict):
                    jobs = data.get('jobs', {})
                    for job_name, job in jobs.items():
                        steps = job.get('steps', [])
                        for step in steps:
                            run_cmd = step.get('run', '')
                            if 'python3 -c' in run_cmd:
                                # Find the python code
                                # This is a bit naive but should catch common cases
                                matches = re.findall(r'python3 -c\s+["\'](.*?)["\']', run_cmd, re.DOTALL)
                                for py_code in matches:
                                    if '\n' in py_code.strip():
                                        if 'textwrap.dedent' not in run_cmd:
                                            file_errors.append(f"Multiline python3 -c block without textwrap.dedent in job '{job_name}'")

                                        # Try to validate the python code
                                        try:
                                            # If it uses dedent in the script, we should simulate it
                                            code_to_check = py_code
                                            if 'textwrap.dedent' in run_cmd:
                                                code_to_check = textwrap.dedent(py_code)
                                            ast.parse(code_to_check)
                                        except SyntaxError as e:
                                            file_errors.append(f"Python syntax error in job '{job_name}': {e}")

                if file_errors:
                    print(f"❌ {filename}:")
                    for err in file_errors:
                        print(f"  - {err}")
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
        print("\nAll workflow files are valid.")

if __name__ == "__main__":
    validate_workflows()
