#!/bin/bash

# ==============================================================================
# Kimi Autonomous Security Auditor Runner
#
# This script sets the necessary environment variables and executes the
# Kimi auditor Python script.
#
# Usage:
#   - Fill in your MOONSHOT_API_KEY below.
#   - Run the script from the root of the repository:
#     bash scripts/run_audit.sh
# ==============================================================================

# --- Configuration ---
# Replace with your actual Moonshot/Kimi API key
export MOONSHOT_API_KEY="sk-your-key-here"

# The Git branch you want to analyze
export TARGET_BRANCH="feat/hubspot-ollama-integration-9809589759324023108"

# The base branch to compare against (usually main or master)
export BASE_BRANCH="main"

# Set to "true" to automatically apply patches and create PRs
export AUTO_FIX="false"

# --- Optional Configuration ---
# export MOONSHOT_BASE_URL="https://api.moonshot.ai/v1"  # Global endpoint
# export KIMI_MODEL="kimi-k2-thinking"
# export WORKSPACE="$(pwd)"

# --- Run the Auditor ---
python3 scripts/kimi_auditor.py
