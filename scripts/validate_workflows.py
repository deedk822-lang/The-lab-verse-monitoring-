
import os
import yaml
import sys

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
                    yaml.safe_load(f)
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
