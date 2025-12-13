#!/bin/bash

# This script validates all GitHub workflow YAML files for syntax errors.

echo "🔍 Validating GitHub workflow YAML files..."

WORKFLOW_DIR=".github/workflows"
EXIT_CODE=0

for file in "$WORKFLOW_DIR"/*.yml "$WORKFLOW_DIR"/*.yaml; do
  if [ -f "$file" ]; then
    echo "Checking: $file"
    if ! python3 -c "import yaml; yaml.safe_load(open('$file'))" 2>/dev/null; then
      echo "❌ Invalid YAML syntax in: $file"
      EXIT_CODE=1
    else
      echo "✅ Valid YAML syntax in: $file"
    fi
  fi
done

if [ $EXIT_CODE -eq 0 ]; then
  echo "✅ All workflow files have valid YAML syntax."
else
    echo "❌ Some workflow files have syntax errors."
fi

exit $EXIT_CODE
