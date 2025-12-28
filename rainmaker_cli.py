"""
Vaal AI Empire - Rainmaker Orchestrator CLI
This script serves as the entry point for the self-healing coding agent.
"""

import asyncio
import sys
import re
import json
import os
from rainmaker_orchestrator.orchestrator import RainmakerOrchestrator

async def main():
    """Main CLI entry point"""
    if len(sys.argv) < 3 or len(sys.argv) > 5:
        print("Usage: python rainmaker_cli.py <task_type> \"<context>\" [<output_filename>] [<model>]")
        print("Example: python rainmaker_cli.py coding_task \"Calculate the 1000th Fibonacci number\" fib.py kimimodel")
        sys.exit(1)

    task_type = sys.argv[1]
    context = sys.argv[2]
    output_filename = sys.argv[3] if len(sys.argv) >= 4 else "output.py"
    model = sys.argv[4] if len(sys.argv) == 5 else "moonshot-v1-8k"


    # --- Security: Filename Validation ---
    if not re.match(r'^[\w\-.]+$', output_filename):
        print("⚠️ WARNING: Invalid filename! Only alphanumeric, hyphens, and periods allowed.")
        print("This prevents path traversal attacks. Use 'script.py' not '../other/script.py'")
        sys.exit(1)

    # --- Initialize Orchestrator ---
    orchestrator = RainmakerOrchestrator(
        workspace_path="./ai_workspace",
        config_file="rainmaker_orchestrator/.env"
    )

    result = None
    try:
        # --- Define the Task ---
        task = {
            "type": task_type,
            "context": context,
            "output_filename": output_filename,
            "model": model
        }
        # --- Execute the Task ---
        result = await orchestrator.execute_task(task)
    finally:
        await orchestrator.aclose()


    if result:
        # --- Print Results ---
        print("\n" + "="*60)
        print("  SELF-HEALING PROTOCOL COMPLETE")
        print("="*60)
        print(f"Status: {result.get('status', 'unknown').upper()}")

        if result.get("status") == "success":
            print(f"✅ Success!")
            print(f"Final Code Path: {result.get('final_code_path')}")
            print(f"Retries: {result.get('retries')}")
            print(f"\n--- Explanation ---")
            print(result.get('explanation', 'N/A'))
            print(f"\n--- Output ---")
            print(result.get('output', 'N/A'))
        else:
            print(f"❌ Failure!")
            print(f"Message: {result.get('message')}")
            last_error = result.get('last_error', {})
            print("\n--- Last Error Details ---")
            print(f"STDOUT: {last_error.get('stdout', 'N/A')}")
            print(f"STDERR: {last_error.get('stderr', 'N/A')}")
            print(f"Message: {last_error.get('message', 'N/A')}")

        print("="*60)


if __name__ == "__main__":
    try:
        workspace = "./ai_workspace"
        if not os.path.exists(workspace):
            os.makedirs(workspace)
            os.chmod(workspace, 0o700)
            print(f"Created workspace at '{workspace}' with secure permissions.")
    except Exception as e:
        print(f"Could not create workspace directory: {e}")
        sys.exit(1)

    asyncio.run(main())
