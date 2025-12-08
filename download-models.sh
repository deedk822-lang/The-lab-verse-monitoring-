#!/bin/bash
set -e

cd ~/localai/models

echo "📥 Downloading AI models..."

# 1. Mistral 7B (Fast, good quality)
echo "Downloading Mistral 7B..."
wget -c https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf

# 2. Llama 3 8B (Meta's latest)
echo "Downloading Llama 3 8B..."
wget -c https://huggingface.co/QuantFactory/Meta-Llama-3-8B-Instruct-GGUF/resolve/main/Meta-Llama-3-8B-Instruct.Q4_K_M.gguf

# 3. Qwen VL (Vision + Language, Chinese support)
echo "Downloading Qwen VL..."
wget -c https://huggingface.co/Qwen/Qwen-VL-Chat/resolve/main/pytorch_model.bin
# Note: Qwen VL requires transformers, see qwen-vl section below

# 4. Phi-3 (Microsoft, very efficient)
echo "Downloading Phi-3..."
wget -c https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf

# 5. CodeLlama (Coding specialist)
echo "Downloading CodeLlama..."
wget -c https://huggingface.co/TheBloke/CodeLlama-7B-Instruct-GGUF/resolve/main/codellama-7b-instruct.Q4_K_M.gguf

# 6. Gemma 2B (Google, very fast)
echo "Downloading Gemma 2B..."
wget -c https://huggingface.co/QuantFactory/gemma-2b-it-GGUF/resolve/main/gemma-2b-it.Q4_K_M.gguf

echo "✅ All models downloaded!"
