
import os
import yaml
import sys
import re

def validate_workflows():
    """
    Validates all YAML files in the .github/workflows directory, including .disabled files.
    """
    workflows_dir = '.github/workflows'
    has_errors = False

    if not os.path.isdir(workflows_dir):
        print(f"Directory not found: {workflows_dir}")
        sys.exit(1)

    # Regex for ternary operators in GitHub Actions expressions: ${{ cond ? val1 : val2 }}
    ternary_re = re.compile(r'\$\{\{.*? \? .*? : .*?\}\}')

    # Regex for python3 -c with multi-line strings that aren't wrapped in textwrap.dedent
    python_c_re = re.compile(r'python3 -c\s+["\']\s*\n')
    dedent_re = re.compile(r'import textwrap; exec\(textwrap.dedent')

    for filename in os.listdir(workflows_dir):
        if filename.endswith('.yml') or filename.endswith('.yaml') or filename.endswith('.disabled'):
            filepath = os.path.join(workflows_dir, filename)
            try:
                with open(filepath, 'r') as f:
                    content = f.read()
                    yaml.safe_load(content)

                file_errors = []

                # Check for ternary operators
                if ternary_re.search(content):
                    file_errors.append("Unsupported ternary operator (?) found in expression.")

                # Check for python3 -c indentation issues
                if python_c_re.search(content) and not dedent_re.search(content):
                    file_errors.append("Multi-line 'python3 -c' block found without 'textwrap.dedent'.")

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

    if has_errors:
        sys.exit(1)
    else:
        print("All workflow files are valid.")

if __name__ == "__main__":
    validate_workflows()
