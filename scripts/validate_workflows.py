
import os
import yaml
import sys
import re

def validate_workflows():
    """
    Validates all YAML files in the .github/workflows directory,
    including .disabled files, and checks for common GHA syntax errors.
    """
    workflows_dir = '.github/workflows'
    has_errors = False

    if not os.path.isdir(workflows_dir):
        print(f"Directory not found: {workflows_dir}")
        sys.exit(1)

    # Regex to find ternary operators in GHA expressions: ${{ ... ? ... : ... }}
    ternary_pattern = re.compile(r'\$\{\{.*?\?.*:.*?\}\}')

    # Regex to find multi-line python3 -c calls that might have indentation issues
    # Matches python3 -c followed by a quote and then a newline and spaces
    python_c_pattern = re.compile(r'python3\s+-c\s+["\']\s*\n\s+')

    for filename in sorted(os.listdir(workflows_dir)):
        if filename.endswith(('.yml', '.yaml', '.disabled')):
            filepath = os.path.join(workflows_dir, filename)
            file_has_errors = False
            try:
                with open(filepath, 'r') as f:
                    content = f.read()
                    # Just to ensure it's valid YAML first
                    yaml.safe_load(content)

                # Check for ternary operators
                if ternary_pattern.search(content):
                    print(f"❌ {filename} - Found unsupported ternary operator syntax in GHA expression.")
                    file_has_errors = True

                # Check for multi-line python3 -c calls without textwrap.dedent
                if python_c_pattern.search(content) and 'textwrap.dedent' not in content:
                    print(f"❌ {filename} - Found potentially problematic multi-line 'python3 -c' call. Use 'import textwrap; exec(textwrap.dedent('''...'''))'.")
                    file_has_errors = True

                if not file_has_errors:
                    print(f"✅ {filename} - OK")
                else:
                    has_errors = True

            except yaml.YAMLError as e:
                print(f"❌ {filename} - Error parsing YAML: {e}")
                has_errors = True
            except Exception as e:
                print(f"❌ {filename} - Unexpected error: {e}")
                has_errors = True

    if has_errors:
        sys.exit(1)
    else:
        print("\nAll workflow files passed comprehensive validation.")

if __name__ == "__main__":
    validate_workflows()
