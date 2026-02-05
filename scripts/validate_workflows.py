
import os
import yaml
import sys
import re
import ast
import textwrap

def validate_workflows():
    """
    Validates all YAML files in the .github/workflows directory for:
    1. Valid YAML syntax
    2. No ternary operators (? :) in GH Actions expressions
    3. Valid Python syntax in multi-line python3 -c commands
    """
    workflows_dir = '.github/workflows'
    has_errors = False

    if not os.path.isdir(workflows_dir):
        print(f"Directory not found: {workflows_dir}")
        sys.exit(1)

    # Regex for GH Actions expressions: ${{ ... }}
    expr_pattern = re.compile(r'\$\{\{\s*(.*?)\s*\}\}')
    # Regex for python3 -c "..."
    py_cmd_pattern = re.compile(r'python3 -c\s+"(.*?)"', re.DOTALL)

    for filename in os.listdir(workflows_dir):
        if filename.endswith('.yml') or filename.endswith('.yaml'):
            filepath = os.path.join(workflows_dir, filename)
            file_errors = []
            try:
                with open(filepath, 'r') as f:
                    content = f.read()
                    data = yaml.safe_load(content)

                # Check for ternary operators in expressions
                for match in expr_pattern.finditer(content):
                    expr = match.group(1)
                    if '?' in expr and ':' in expr:
                        # Simple check, might have false positives if ? or : are in strings
                        # but in GH expressions they usually aren't used that way except for ternary
                        file_errors.append(f"Potential invalid ternary operator in expression: ${{{{{expr}}}}}")

                # Check for Python syntax in python3 -c commands
                for match in py_cmd_pattern.finditer(content):
                    py_code = match.group(1)
                    if '\n' in py_code:
                        try:
                            # Try to parse it as is
                            ast.parse(py_code)
                        except IndentationError:
                            # Check if it would work with dedent
                            try:
                                ast.parse(textwrap.dedent(py_code))
                                file_errors.append(f"Indentation error in multi-line python3 -c command. Should use textwrap.dedent.")
                            except Exception as e:
                                file_errors.append(f"Python syntax error in multi-line command: {e}")
                        except Exception as e:
                            file_errors.append(f"Python syntax error in multi-line command: {e}")

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
