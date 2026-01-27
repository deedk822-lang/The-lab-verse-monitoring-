#!/usr/bin/env bash
set -euo pipefail

TARBALL="${TARBALL:-autoglm_sa.tar.gz}"
DIR="${DIR:-autoglm_sa}"

echo "🇿🇦 AutoGLM South Africa Edition Installer"
echo "======================================"
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

[[ -f "$TARBALL" ]] || { echo "❌ Error: $TARBALL not found!"; exit 1; }

echo "🔍 Checking system requirements..."
for cmd in python3 git adb; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "❌ $cmd is required but not installed."; exit 1; }
done
echo "✅ System requirements met"

echo "📦 Extracting package..."
rm -rf "$DIR"
tar -xzf "$TARBALL"

[[ -d "$DIR/Open-AutoGLM" ]] || { echo "❌ Open-AutoGLM directory not found in package!"; exit 1; }

cd "$DIR/Open-AutoGLM"

echo "📦 Installing Open-AutoGLM dependencies..."
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

echo ""
echo "✅ AutoGLM South Africa Edition installed successfully!"
echo ""
echo "📋 Next steps:"
echo "   1. Edit configuration: cd $DIR && nano config.env"
echo "   2. Set your API key in config.env"
echo "   3. Start AutoGLM: ./start_autoglm.sh"
echo ""
echo "📚 Documentation: $DIR/README_SA.md"
echo "🤝 Community support: +27 XX XXX XXXX"
echo ""
echo "🌐 For API key: https://docs.z.ai/api-reference/introduction"
