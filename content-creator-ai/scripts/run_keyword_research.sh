#!/bin/bash

# Keyword Research with Perplexity Deep Search
# Usage: ./run_keyword_research.sh <csv_file> [num_topics] [top_n_deep_search]

CSV_FILE=${1:-"data/remote_teams.csv"}
NUM_TOPICS=${2:-4}
DEEP_SEARCH_TOP_N=${3:-3}

echo "🚀 Starting Enhanced Keyword Research"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "CSV File: $CSV_FILE"
echo "Topics: $NUM_TOPICS"
echo "Deep Search Top N: $DEEP_SEARCH_TOP_N"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python3 services/keywordResearchWithPerplexity.py \
  --csv-path "$CSV_FILE" \
  --num-topics "$NUM_TOPICS" \
  --enable-deep-search true \
  --deep-search-top-n "$DEEP_SEARCH_TOP_N"

echo ""
echo "✅ Complete! Check keyword_research_output/ for results"
