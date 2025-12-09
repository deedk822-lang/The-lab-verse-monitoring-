#!/bin/bash
set -e

echo "🛡️ INITIATING PRE-FLIGHT INTEGRITY CHECK..."

# 1. FIX PYTHON PACKAGING (Missing __init__.py)
# Without these, 'from src.core import ...' fails in many environments.
echo "   - Injecting package markers..."
touch vaal-ai-empire/src/__init__.py
touch vaal-ai-empire/src/core/__init__.py
touch vaal-ai-empire/src/tools/__init__.py
touch vaal-ai-empire/src/agents/__init__.py
touch vaal-ai-empire/src/products/__init__.py

# 2. CONSOLIDATE REQUIREMENTS (The Truth Source)
# We merge all the tools we installed (Jira, Qwen, Aliyun, etc.) into one file.
echo "   - Consolidating dependencies..."
cat << 'EOF' > vaal-ai-empire/requirements.txt
qwen-agent>=0.0.6
oss2>=2.18.4
mistralai>=1.0.0
cohere>=5.5.0
pandas>=2.2.0
python-dotenv>=1.0.1
dashscope>=1.20.0
huggingface_hub>=0.23.0
pypdf>=4.2.0
jira>=3.8.0
notion-client>=2.2.1
requests>=2.31.0
fastapi>=0.111.0
uvicorn>=0.30.0
python-multipart>=0.0.9
PyGithub>=2.3.0
yfinance>=0.2.40
ta>=0.11.0
python-wordpress-xmlrpc>=2.3
mailchimp-marketing>=3.0.80
EOF

# 3. FIX PERMISSIONS
# Make sure all shell scripts are executable.
echo "   - Fixing script permissions..."
chmod +x vaal-ai-empire/scripts/*.sh

# 4. SYNTAX VALIDATION (The Compiler Check)
# We try to compile every python file. If one has a syntax error, we stop NOW.
echo "   - verifying Python syntax..."
find vaal-ai-empire -name "*.py" | while read file; do
    python3 -m py_compile "$file"
    if [ $? -ne 0 ]; then
        echo "❌ SYNTAX ERROR in $file"
        exit 1
    fi
done

# 5. VERIFY CRITICAL IMPORTS
# We check if the Master Agent can actually find its brain.
echo "   - Verifying module linkage..."
export PYTHONPATH=$(pwd)

python3 -c "
import sys
try:
    from services.content_generator import ContentFactory
    print('   ✅ Core Module Linkage: OK')
except ImportError as e:
    print(f'   ❌ LINKAGE BROKEN: {e}')
    sys.exit(1)
"

echo "✅ PRE-FLIGHT CHECK PASSED."
echo "   - Package Structure: VALID"
echo "   - Requirements: CONSOLIDATED"
echo "   - Syntax: CLEAN"
echo "   - System is ready for Merge/Review."
