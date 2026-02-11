
import os
import yaml
import sys
import re

def validate_workflows():
    """
    Validates all YAML files in the .github/workflows directory,
    including .disabled files, and checks for common syntax errors.
    """
    workflows_dir = '.github/workflows'
    has_errors = False

    if not os.path.isdir(workflows_dir):
        print(f"Directory not found: {workflows_dir}")
        sys.exit(1)

    # Regex for ternary operator in GH expressions: ${{ condition ? val1 : val2 }}
    ternary_pattern = re.compile(r'\${{.*? \? .*? : .*?}}')

    # Regex for python3 -c with potential indentation issues
    # Matches python3 -c " or ' followed by a newline and then indented code
    python_c_pattern = re.compile(r'python3 -c\s+["\']\s*\n\s+')

    files = [f for f in os.listdir(workflows_dir)
             if f.endswith('.yml') or f.endswith('.yaml') or f.endswith('.yml.disabled')]

    for filename in files:
        filepath = os.path.join(workflows_dir, filename)
        file_errors = False
        try:
            with open(filepath, 'r') as f:
                content = f.read()
                # Validate YAML structure
                yaml.safe_load(content)

            # Check for ternary operator
            if ternary_pattern.search(content):
                print(f"❌ {filename} - Error: Found unsupported ternary operator in expression")
                file_errors = True

            # Check for python3 -c indentation
            if python_c_pattern.search(content):
                # Check if it uses textwrap.dedent
                if 'textwrap.dedent' not in content:
                    print(f"❌ {filename} - Error: Multi-line python3 -c detected without textwrap.dedent")
                    file_errors = True

            if not file_errors:
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
        print("\nAll workflow files are valid (including syntax checks).")

if __name__ == "__main__":
    validate_workflows()
