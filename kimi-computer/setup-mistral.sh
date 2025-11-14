#!/bin/bash
# setup-mistral.sh

# Create a models directory if it doesn't exist
mkdir -p models

# Create a model file for Mistral-7B
cat << EOF > models/mistral-7b-instruct.gguf
---
name: mistral-7b-instruct
urls:
- https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/mistral-7b-instruct-v0.1.Q4_K_M.gguf
sha256: "5b28c00de38a3c8e434f1dd45163f35f29f1b2b6c7a31505342a49f50e82c18d"
inference:
  # ... (omitted for brevity)
...
EOF

echo "Mistral-7B model file created. LocalAI will download it on first run."
echo "Run 'docker-compose up -d' to start the application."
