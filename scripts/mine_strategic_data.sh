#!/bin/bash
set -e

echo "⛏️ INITIATING STRATEGIC DATA MINING..."
echo "   - Source: Kaggle API"
echo "   - Targets: Tech Salaries, Economic Indicators"

# 1. VERIFY CREDENTIALS
if [ -z "$KAGGLE_USERNAME" ] || [ -z "$KAGGLE_KEY" ]; then
    echo "❌ Error: Kaggle Credentials missing from environment."
    echo "   Action: Export KAGGLE_USERNAME and KAGGLE_KEY."
    exit 1
fi

# 2. PREPARE DATA VAULT
DATA_DIR="vaal-ai-empire/data/strategic"
mkdir -p "$DATA_DIR"

# 3. MINE DATASET 1: DEVELOPER SALARIES (For VanHack Agent)
# Dataset: Stack Overflow Developer Survey (Good for salary benchmarking)
echo "   > Downloading: Developer Salary Data..."
kaggle datasets download -d stackoverflow/stack-overflow-2023-developer-survey -p "$DATA_DIR/salaries" --unzip --force

# 4. MINE DATASET 2: ECONOMIC INDICATORS (For JSE/Tax Agent)
# Dataset: World Bank Data (South Africa filter)
echo "   > Downloading: Global Economic Indicators..."
kaggle datasets download -d worldbank/world-development-indicators -p "$DATA_DIR/economics" --unzip --force

# 5. CREATE THE ANALYSIS TOOL
# We create a python tool that Qwen uses to read this specific data.

mkdir -p vaal-ai-empire/src/tools

cat << 'EOF' > vaal-ai-empire/src/tools/data_miner.py
import pandas as pd
import os
import logging
from qwen_agent.tools.base import BaseTool, register_tool

logger = logging.getLogger("DataMiner")

@register_tool('salary_benchmarker')
class SalaryBenchmarker(BaseTool):
    description = 'Queries downloaded Kaggle data to benchmark developer salaries.'
    parameters = [{'name': 'role', 'type': 'string', 'required': True}]

    def call(self, params: str, **kwargs) -> str:
        # Load the downloaded CSV
        csv_path = "vaal-ai-empire/data/strategic/salaries/survey_results_public.csv"
        if not os.path.exists(csv_.path): return "Data not found. Run mining script."

        try:
            df = pd.read_csv(csv_path, usecols=['DevType', 'ConvertedCompYearly', 'Country'])

            # Filter for South Africa vs Global
            sa_data = df[df['Country'] == 'South Africa']
            global_data = df[df['Country'].isin(['United States', 'Canada', 'Germany'])]

            # Calculate Averages (Simplified logic)
            sa_avg = sa_data['ConvertedCompYearly'].median()
            global_avg = global_data['ConvertedCompYearly'].median()

            return f"BENCHMARK:\nSA Median: ${sa_avg:,.2f}\nGlobal Median: ${global_avg:,.2f}\nArbitrage Gap: ${global_avg - sa_avg:,.2f}"
        except Exception as e:
            return f"Analysis Error: {e}"
EOF

echo "✅ MINING COMPLETE."
echo "   - Data stored in: $DATA_DIR"
echo "   - Tool Created: src/tools/data_miner.py"
