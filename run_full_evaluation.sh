#!/bin/bash
# Master Evaluation and Improvement Pipeline
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
REPO_PATH="${REPO_PATH:-.}"
OLLAMA_URL="${OLLAMA_URL:-http://localhost:11434}"
MODEL="${MODEL:-codellama}"
OUTPUT_DIR="${OUTPUT_DIR:-./evaluation_results}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$OUTPUT_DIR"

print_header() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  🚀 COMPREHENSIVE EVALUATION & IMPROVEMENT PIPELINE      ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
}

print_section() {
    echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

run_evaluation() {
    print_section "🧪 PHASE 1: Running Comprehensive Evaluation" >&2
    EVAL_OUTPUT="$OUTPUT_DIR/evaluation_${TIMESTAMP}.json"
    python3 evaluation_system.py --repo-path "$REPO_PATH" --model "$MODEL" --ollama-url "$OLLAMA_URL" --output "$EVAL_OUTPUT" >&2
    echo "$EVAL_OUTPUT"
}

run_improvement_cycle() {
    print_section "🔄 PHASE 2: Running Improvement Cycle"
    local eval_file=$1
    IMPROVE_OUTPUT="$OUTPUT_DIR/improvements_${TIMESTAMP}.md"
    python3 continuous_improvement.py "$eval_file" --repo-path "$REPO_PATH" --model "$MODEL" --ollama-url "$OLLAMA_URL" --report "$IMPROVE_OUTPUT"
}

run_benchmarking() {
    print_section "⚡ PHASE 3: Running Model Benchmarking"
    BENCHMARK_OUTPUT="$OUTPUT_DIR/benchmark_${TIMESTAMP}.json"
    python3 benchmarking_system.py --models "$MODEL" --ollama-url "$OLLAMA_URL" --output "$BENCHMARK_OUTPUT"
}

run_unit_tests() {
    print_section "🧪 PHASE 4: Running Unit Tests"
    python3 -m pytest tests/unit/ -v --tb=short
}

main() {
    print_header

    # Check if AI provider is available (optional but good for logs)
    if ! curl -s --max-time 2 "$OLLAMA_URL/api/tags" > /dev/null && [ -z "$MOONSHOT_API_KEY" ] && [ -z "$KIMI_API_KEY" ] && [ -z "$COHER_API_KEY" ]; then
        echo -e "${YELLOW}⚠ Warning: No AI provider reachable. Some tests will be skipped.${NC}"
    fi

    eval_file=$(run_evaluation)
    run_improvement_cycle "$eval_file"
    run_benchmarking
    run_unit_tests

    echo -e "\n${GREEN}✅ PIPELINE COMPLETE. Results in $OUTPUT_DIR${NC}"
}

main
