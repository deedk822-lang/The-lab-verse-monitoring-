#!/bin/bash

# ==============================================================================
# Kimi Autonomous Security Auditor v4 Runner
#
# This script sets the necessary environment variables and executes the
# Kimi auditor v4 Python script.
#
# Usage:
#   - Fill in your MOONSHOT_API_KEY below.
#   - Run the script from the root of the repository:
#     bash scripts/run_audit_v4.sh
# ==============================================================================

# --- Configuration ---
# Replace with your actual Moonshot/Kimi API key
export MOONSHOT_API_KEY="sk-your-key-here"

# The Git branch you want to analyze
export TARGET_BRANCH="feat/hubspot-ollama-integration-9809589759324023108"

# The base branch to compare against (usually main or master)
export BASE_BRANCH="main"

# Set to "true" to automatically approve and apply patches
export AUTO_APPROVE="false"

# The command to run your test suite
export TEST_CMD="pytest"

# The maximum number of times Kimi should attempt to refine a patch
export MAX_ITERATIONS="3"

# --- Optional Configuration ---
# export MOONSHOT_BASE_URL="https://api.moonshot.ai/v1"  # Global endpoint
# export KIMI_MODEL="kimi-k2-thinking"
# export WORKSPACE="$(pwd)"

# --- Run the Auditor ---
python3 scripts/kimi_auditor_v4.py
