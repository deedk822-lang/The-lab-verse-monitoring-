#!/bin/bash
# AutoGLM South Africa Edition - Verification Script
echo "🔍 AutoGLM South Africa Edition Verification"
echo "======================================"
echo ""

# Check installer script
if [ -f "install_sa.sh" ]; then
    echo "✅ Installer script: install_sa.sh"
else
    echo "❌ Installer script missing: install_sa.sh"
fi

# Check package file
if [ -f "autoglm_sa.tar.gz" ]; then
    echo "✅ Package file: autoglm_sa.tar.gz"

    # Check package integrity
    if tar -tzf autoglm_sa.tar.gz >/dev/null 2>&1; then
        echo "✅ Package integrity: OK"
    else
        echo "❌ Package integrity: CORRUPTED"
    fi
else
    echo "❌ Package file missing: autoglm_sa.tar.gz"
fi

# Check package contents
echo ""
echo "📦 Package contents:"
if [ -f "autoglm_sa.tar.gz" ]; then
    tar -tzf autoglm_sa.tar.gz | head -10
    echo "   ... (and more)"
fi

echo ""
echo "📋 Installation command:"
echo "   ./install_sa.sh"
