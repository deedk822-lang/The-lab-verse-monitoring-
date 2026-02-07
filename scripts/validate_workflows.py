
import os
import yaml
import sys
import re
import ast
import textwrap

def validate_workflows():
    """
    Validates all YAML files in the .github/workflows directory,
    including expression syntax and embedded Python scripts.
    """
    workflows_dir = '.github/workflows'
    has_errors = False

    if not os.path.isdir(workflows_dir):
        print(f"Directory not found: {workflows_dir}")
        sys.exit(1)

    # Regex to find GHA expressions ${{ ... }}
    expression_pattern = re.compile(r'\${{\s*(.*?)\s*}}')

    def check_expressions(value, filename, step_context):
        errors = False
        if isinstance(value, str):
            for match in expression_pattern.finditer(value):
                expr = match.group(1)
                if '?' in expr and ':' in expr:
                    # Check if this is a github-script
                    if step_context.get('uses', '').startswith('actions/github-script'):
                        continue
                    print(f"❌ {filename} - Potential invalid ternary operator in expression: ${{{{{expr}}}}}")
                    errors = True
        elif isinstance(value, dict):
            for k, v in value.items():
                if check_expressions(v, filename, step_context):
                    errors = True
        elif isinstance(value, list):
            for item in value:
                if check_expressions(item, filename, step_context):
                    errors = True
        return errors

    for filename in os.listdir(workflows_dir):
        if filename.endswith('.yml') or filename.endswith('.yaml') or filename.endswith('.yml.disabled'):
            filepath = os.path.join(workflows_dir, filename)
            file_has_errors = False
            try:
                with open(filepath, 'r') as f:
                    content = f.read()
                    data = yaml.safe_load(content)

                # Deep validation of the YAML structure
                if isinstance(data, dict) and 'jobs' in data:
                    for job_name, job in data['jobs'].items():
                        if 'steps' in job:
                            for step in job['steps']:
                                # Check expressions in ALL step fields
                                if check_expressions(step, filename, step):
                                    file_has_errors = True

                                # Check embedded Python in 'run' blocks
                                if 'run' in step:
                                    run_content = step['run']
                                    if 'python3 -c' in run_content:
                                        # Extract the python code
                                        # Heuristic to find the code inside quotes
                                        py_match = re.search(r'python3 -c\s+["\'](.*?)["\']', run_content, re.DOTALL)
                                        if not py_match:
                                             py_match = re.search(r'python3 -c\s+"""(.*?)"""', run_content, re.DOTALL)

                                        if py_match:
                                            py_code = py_match.group(1)

                                            # Check if it uses textwrap.dedent
                                            if 'textwrap.dedent' not in run_content:
                                                # Check for indentation errors
                                                try:
                                                    ast.parse(py_code)
                                                except SyntaxError as e:
                                                    print(f"❌ {filename} - Python syntax error in run block: {e}")
                                                    file_has_errors = True
                                            else:
                                                # If it uses textwrap.dedent, we assume it's handled
                                                pass

                if not file_has_errors:
                    print(f"✅ {filename} - OK")
                else:
                    has_errors = True

            except yaml.YAMLError as e:
                print(f"❌ {filename} - Error parsing YAML: {e}")
                has_errors = True
            except Exception as e:
                print(f"❌ {filename} - Unexpected error processing {filename}: {e}")
                has_errors = True

    if has_errors:
        sys.exit(1)
    else:
        print("All workflow files are valid.")

if __name__ == "__main__":
    validate_workflows()
