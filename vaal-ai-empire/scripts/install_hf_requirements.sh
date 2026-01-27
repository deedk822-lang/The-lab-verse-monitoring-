#!/bin/bash
set -e
echo "🧪 Installing Hugging Face Lab Dependencies..."
pip install huggingface_hub sentence-transformers --upgrade --quiet
