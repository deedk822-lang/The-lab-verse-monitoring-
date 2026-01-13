#!/bin/bash
set -e

echo "🔍 Running pre-commit validation..."

# Type safety
echo "1/6 Type checking..."
mypy api/ --strict

# Linting
echo "2/6 Linting..."
ruff check api/ tests/

# Formatting
echo "3/6 Format check..."
black --check api/ tests/

# Tests
echo "4/6 Running tests..."
pytest tests/ -v --cov --cov-fail-under=90

# Security
echo "5/6 Security scan..."
bandit -r api/ -ll

# Dependencies
echo "6/6 Dependency audit..."
pip-audit

echo "✅ All checks passed!"
