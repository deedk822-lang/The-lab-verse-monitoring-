#!/bin/bash
set -e

echo "🇿🇦 INITIATING OPERATION: SA SHOWCASE..."
echo "   - Mission: Generate 'VAAL_EMPIRE_PORTFOLIO.md'"
echo "   - Agents: Content Studio, Titan Brain, Guardian"

cat << 'EOF' > vaal-ai-empire/scripts/run_showcase.py
import sys
import os
import json

# Add source to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from src.products.content_studio import ContentStudio
    from src.agents.tax_collector import TaxAgentMaster
except ImportError as e:
    print(f"❌ Import Error: {e}")
    sys.exit(1)

def build_portfolio():
    print("🚀 CONTACTING AI WORKFORCE...")

    portfolio = "# 🦁 THE VAAL AI EMPIRE: CAPABILITY SHOWCASE\n\n"

    # 1. MARKETING DEMO
    print("   > [Content Studio] Creating Launch Campaign...")
    studio = ContentStudio()
    if studio.client:
        post = studio.generate_social_bundle(
            "AI Automation Agency",
            "Launching world-class AI services for businesses in Vanderbijlpark.
"
        )
        portfolio += "## 1. MARKETING AUTOMATION\n"
        portfolio += f"**Output:** {post.get('caption')}\n\n"

    # 2. STRATEGY DEMO (Titan Brain)
    print("   > [Titan Brain] Analyzing Section 12B Tax...")
    agent = TaxAgentMaster()
    # Force Titan Mode
    agent.set_model('deepseek-v3')

    # Real Mission: Analyze Solar Tax Incentive
    if agent.titan:
        mission = "Analyze South Africa's Section 12B Tax Allowance for Solar En
ergy."
        data = {"investment": "R1,000,000", "goal": "Maximize Deduction"}
        result = agent.titan.solve_critical_mission(mission, data)

        portfolio += "## 2. STRATEGIC INTELLIGENCE\n"
        if "final_deliverable" in result:
            portfolio += f"```text\n{result['final_deliverable']}\n```\n\n"

    # SAVE
    with open("VAAL_EMPIRE_PORTFOLIO.md", "w") as f:
        f.write(portfolio)

    print("\n🎉 SHOWCASE GENERATED: 'VAAL_EMPIRE_PORTFOLIO.md'")

if __name__ == "__main__":
    build_portfolio()
EOF

# Execute
python3 vaal-ai-empire/scripts/run_showcase.py
