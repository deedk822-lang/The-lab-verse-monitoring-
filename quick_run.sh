#!/bin/bash
# Quick Run - PR Fix Agent
# Execute this to test the system immediately

set -e

echo "🚀 PR Fix Agent - Quick Run"
echo "=============================="
echo ""

# Check if running in correct directory
if [ ! -f "orchestrator_production.py" ]; then
    echo "❌ Error: orchestrator_production.py not found"
    echo "   Run this from the outputs directory"
    exit 1
fi

# Make scripts executable
chmod +x orchestrator_production.py
chmod +x setup.sh

# Check Python dependencies
echo "📦 Checking Python dependencies..."
python3 -c "import ollama" 2>/dev/null || {
    echo "Installing ollama-python..."
    pip install ollama --quiet
}

# Check if Ollama is running
echo "🤖 Checking Ollama service..."
if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "❌ Ollama not running"
    echo "   Start with: docker run -d -p 11434:11434 ollama/ollama"
    echo "   Or use HuggingFace: --backend huggingface"
    echo ""
    echo "📝 Running in TEST mode (mock LLM)..."
    MOCK_MODE=true
else
    echo "✅ Ollama is running"
    MOCK_MODE=false

    # Check if model exists
    if ! docker exec -it $(docker ps -q -f ancestor=ollama/ollama) ollama list | grep -q "qwen2.5-coder"; then
        echo "📥 Downloading qwen2.5-coder:1.5b (this may take a few minutes)..."
        docker exec -it $(docker ps -q -f ancestor=ollama/ollama) ollama pull qwen2.5-coder:1.5b
    fi
fi

# Run orchestrator
echo ""
echo "🔍 Analyzing test findings..."
echo ""

if [ "$MOCK_MODE" = true ]; then
    # Create mock analysis for testing
    cat > proposals.json <<'EOF'
[
  {
    "finding": {
      "file": "src/api/routes/auth.py",
      "line_start": 45,
      "line_end": 47,
      "severity": "high",
      "category": "security",
      "issue": "Hardcoded password",
      "suggestion": "Use environment variables",
      "code_snippet": "password = 'admin123'"
    },
    "root_cause": "Credentials stored directly in source code",
    "fix_approach": "Move to environment variable with validation",
    "expected_changes": ["Add PASSWORD env var", "Update auth.py line 45"],
    "risk_level": "low",
    "test_requirements": ["Test login with new env var", "Verify old code removed"]
  }
]
EOF
    echo "✅ Created mock proposals (Ollama not available)"
else
    # Run actual analysis
    python3 orchestrator_production.py review \
        --findings test_findings.json \
        --backend ollama \
        --limit 3 \
        --output proposals.json
fi

# Show results
if [ -f proposals.json ]; then
    echo ""
    echo "📊 Results:"
    echo "==========="

    # Count proposals
    count=$(python3 -c "import json; print(len(json.load(open('proposals.json'))))")
    echo "✅ Generated $count proposals"
    echo ""

    # Show first proposal
    echo "📄 Sample Proposal:"
    python3 -c "
import json
with open('proposals.json') as f:
    proposals = json.load(f)
    if proposals:
        p = proposals[0]
        print(f\"  File: {p['finding']['file']}:{p['finding']['line_start']}\")
        print(f\"  Issue: {p['finding']['issue']}\")
        print(f\"  Root Cause: {p['root_cause']}\")
        print(f\"  Fix: {p['fix_approach']}\")
        print(f\"  Risk: {p['risk_level']}\")
" 2>/dev/null || cat proposals.json | head -20

    echo ""
    echo "✅ Success! Check proposals.json for full results"
else
    echo "❌ No proposals generated"
    exit 1
fi

# Show next steps
echo ""
echo "🎯 Next Steps:"
echo "=============="
echo ""
echo "1. Review proposals:"
echo "   cat proposals.json | jq ."
echo ""
echo "2. Run with more findings:"
echo "   python3 orchestrator_production.py review --findings test_findings.json --limit 10"
echo ""
echo "3. Deploy full stack:"
echo "   ./setup.sh"
echo ""
echo "4. Test with HuggingFace:"
echo "   export HF_API_TOKEN=hf_xxx"
echo "   python3 orchestrator_production.py review --backend huggingface --findings test_findings.json"
echo ""
