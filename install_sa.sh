#!/bin/bash
# AutoGLM South Africa Edition - Installer
echo "🇿🇦 AutoGLM South Africa Edition Installer"
echo "====================================="
echo "Date: $(date)"
echo ""

# Check if package file exists
if [ ! -f "autoglm_sa.tar.gz" ]; then
    echo "❌ Error: autoglm_sa.tar.gz not found!"
    echo "Please download both install_sa.sh and autoglm_sa.tar.gz"
    exit 1
fi

# Check if this script is executable
if [ ! -x "$0" ]; then
    echo "⚠️ Making script executable..."
    chmod +x "$0"
    echo "✅ Script made executable"
    echo ""
    echo "Please run the installer again:"
    echo "./$0"
    exit 0
fi

# Extract package
echo "📦 Extracting package..."
tar -xzf autoglm_sa.tar.gz

# Check if extraction was successful
if [ ! -d "autoglm_sa" ]; then
    echo "❌ Error: Package extraction failed!"
    exit 1
fi

# Change to package directory
cd autoglm_sa

# Check if setup script exists
if [ ! -f "setup_sa.sh" ]; then
    echo "❌ Error: setup_sa.sh not found in package!"
    exit 1
fi

# Run setup script
echo "🚀 Running setup..."
./setup_sa.sh

# Check setup result
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ AutoGLM South Africa Edition installed successfully!"
    echo ""
    echo "📋 Next steps:"
    echo "   cd autoglm_sa"
    echo "   ./start_autoglm.sh"
    echo ""
    echo "📚 Documentation: README_SA.md"
    echo "🤝 Community support: +27 XX XXX XXXX"
else
    echo ""
    echo "❌ Setup failed! Please check the error messages above."
    exit 1
fi
