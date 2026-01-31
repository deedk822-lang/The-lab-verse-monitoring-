#!/bin/bash
# Local PR Fix Agent for Codespace

echo "🦙 Starting Ollama in Codespace..."
ollama serve &> /tmp/ollama.log &
sleep 3

echo "🧠 Loading models..."
ollama pull codellama:7b
ollama pull mistral:7b
ollama pull llama3.2

echo "🔍 Running checks..."
# Type check
mypy src/ --ignore-missing-imports > /tmp/type_err.txt 2>&1

# Security
bandit -r src/ -f txt > /tmp/sec_err.txt 2>&1

# Lint
ruff check src/ > /tmp/lint_err.txt 2>&1

echo "🤖 Analyzing with AI..."

# Python script to analyze and fix using Kimi Code CLI
python3 << 'PY'
import subprocess
import json

def ollama_fix(error_file, model):
    with open(error_file) as f:
        errors = f.read()[:2000]

    if not errors.strip():
        return "No errors found"

    # Use Kimi Code if installed, otherwise use Ollama directly
    cmd = [
        "kimi", "ask",
        f"Fix these errors: {errors}",
        "--model", model,
        "--no-stream"
    ]

    try:
        # Try Kimi CLI first
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            return result.stdout
        raise Exception("Kimi CLI failed")
    except Exception:
        # Fallback to Ollama directly
        import ollama
        # Map local model names to Ollama model names
        model_map = {
            "codellama-local": "codellama:7b",
            "mistral-local": "mistral:7b",
            "llama32-local": "llama3.2"
        }
        target_model = model_map.get(model, model)
        try:
            response = ollama.chat(
                model=target_model,
                messages=[{'role': 'user', 'content': f"Fix these errors: {errors}"}]
            )
            return response['message']['content']
        except Exception as e:
            return f"Fallback to Ollama failed: {str(e)}"

print("Type fixes:", ollama_fix("/tmp/type_err.txt", "codellama-local"))
print("Security fixes:", ollama_fix("/tmp/sec_err.txt", "mistral-local"))
print("Lint fixes:", ollama_fix("/tmp/lint_err.txt", "llama32-local"))
PY

echo "✅ Analysis complete!"
