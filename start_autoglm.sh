#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/config.env"
OPENGLM_DIR="$SCRIPT_DIR/Open-AutoGLM"
VENV_DIR="$OPENGLM_DIR/venv"

echo "🤖 Starting AutoGLM SA..."
echo "📁 Script directory: $SCRIPT_DIR"

[[ -f "$CONFIG_FILE" ]] || { echo "❌ Missing $CONFIG_FILE"; exit 1; }
source "$CONFIG_FILE

[[ -n "${PHONE_AGENT_API_KEY:-}" && "${PHONE_AGENT_API_KEY:-}" != "PUT_YOUR_ZAI_API_KEY_HERE" ]] || {
  echo "❌ Set PHONE_AGENT_API_KEY in config.env"
  exit 1
}

[[ -d "$OPENGLM_DIR" ]] || { echo "❌ Missing $OPENGLM_DIR (reinstall)"; exit 1; }
[[ -d "$VENV_DIR" ]] || { echo "❌ Missing venv (run install_sa.sh)"; exit 1; }

source "$VENV_DIR/bin/activate"

cd "$OPENGLM_DIR"

if [[ $# -eq 0 ]]; then
  python main.py
else
  python main.py "$@"
fi
