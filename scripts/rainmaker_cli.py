# scripts/rainmaker_cli.py

import asyncio
import sys
import os
import json

# Adjust path to import orchestrator
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from rainmaker_orchestrator.auto_switch import AdaptiveModelRouter
from rainmaker_orchestrator.orchestrator import RainmakerOrchestrator

async def main():
    """CLI for the Rainmaker Agent"""

    if len(sys.argv) < 3:
        print("Usage: python rainmaker_cli.py <task_type> <file_or_text>")
        print("Task types: code_debugging, strategy, ingestion, extraction")
        sys.exit(1)

    task_type = sys.argv[1]
    input_data = sys.argv[2]

    # Load context
    if os.path.exists(input_data):
        with open(input_data, 'r') as f:
            context = f.read()
        print(f"📄 Loaded {len(context)} characters from {input_data}")
    else:
        context = input_data
        print(f"📝 Using direct input: {context[:100]}...")

    # Build task
    task = {
        "type": task_type,
        "context": context,
        "priority": "high"
    }

    # Route and execute
    orchestrator = RainmakerOrchestrator()
    router = AdaptiveModelRouter(orchestrator)

    print(f"\n🧠 Routing task...")
    routing = orchestrator.route_task(task)
    print(f"   Model: {routing['model']}")
    print(f"   Reason: {routing['reason']}")
    print(f"   Estimated cost: ${routing['estimated_cost']:.4f}")
    print(f"   Context size: {routing['context_size']:,} tokens\n")

    print("⚙️  Executing...")
    result = await router.execute_with_fallback(task)

    # Output
    if "fallback_from" in result:
        print(f"⚠️  Fallback from {result['fallback_from']}")

    print("\n" + "="*50)
    print("RESPONSE:")
    print("="*50)
    print(result["response"]["choices"][0]["message"]["content"])
    print("="*50)

if __name__ == "__main__":
    asyncio.run(main())
