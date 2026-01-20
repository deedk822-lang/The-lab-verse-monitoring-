#!/bin/bash
# South Africa AutoGLM Installer

echo "🇿🇦 Installing AutoGLM South Africa Edition..."

# Extract package
tar -xzf autoglm_sa.tar.gz

# Run setup
cd autoglm_sa
./setup_sa.sh

echo "✅ AutoGLM SA Edition installed!"
echo "📞 Community support: +27 XX XXX XXXX"
