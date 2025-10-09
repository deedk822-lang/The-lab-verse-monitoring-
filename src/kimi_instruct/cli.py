import argparse
import asyncio
import json
import aiohttp

async def get_status(args):
    """
    Fetches and displays the project status from the Kimi service.
    """
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("http://localhost:8084/status") as response:
                response.raise_for_status()
                status = await response.json()
                if args.output == 'json':
                    print(json.dumps(status, indent=2))
                else:
                    print_status_table(status)
        except aiohttp.ClientError as e:
            print(f"Error: Could not connect to Kimi service at http://localhost:8084. Is it running?")
            print(f"Details: {e}")

async def create_task(args):
    """
    Sends a request to the Kimi service to create a new task.
    """
    payload = {
        "title": args.title,
        "description": args.description,
        "priority": args.priority
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post("http://localhost:8084/tasks", json=payload) as response:
                response.raise_for_status()
                result = await response.json()
                print(f"Task created successfully. Task ID: {result['task_id']}")
        except aiohttp.ClientError as e:
            print(f"Error: Could not create task via Kimi service.")
            print(f"Details: {e}")

def print_status_table(status):
    """
    Pretty-prints the status report in a table format.
    """
    print("\n" + " Kimi Instruct Status Report ".center(50, '🎯'))
    print("=" * 50)

    context = status.get('project_context', {})
    summary = status.get('task_summary', {})

    print(f"Timestamp: {status.get('timestamp')}")
    print("-" * 50)
    print("PROJECT CONTEXT")
    print(f"  Phase: {context.get('current_phase')}")
    print(f"  Risk Level: {context.get('risk_level')}")
    print(f"  Timeline: {context.get('timeline_status')}")
    print(f"  Budget Left: ${context.get('budget_remaining'):.2f}")

    print("-" * 50)
    print("TASK SUMMARY")
    print(f"  Total Tasks: {summary.get('total')}")
    print(f"  Completed: {summary.get('completed')}")
    print(f"  Progress: {summary.get('completion_percentage'):.1f}%")
    print("=" * 50)

async def main():
    parser = argparse.ArgumentParser(description="Command-line interface for the Kimi Instruct AI Project Manager")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    # 'status' command
    parser_status = subparsers.add_parser('status', help="Get the current project status report.")
    parser_status.add_argument("--output", choices=['json', 'table'], default='table', help="Output format.")
    parser_status.set_defaults(func=get_status)

    # 'create-task' command
    parser_create = subparsers.add_parser('create-task', help="Create a new task for Kimi to manage.")
    parser_create.add_argument("--title", required=True, help="The title of the task.")
    parser_create.add_argument("--description", default="", help="A brief description of the task.")
    parser_create.add_argument("--priority", choices=['low', 'medium', 'high', 'critical'], default='medium', help="The priority of the task.")
    parser_create.set_defaults(func=create_task)

    args = parser.parse_args()
    await args.func(args)

if __name__ == "__main__":
    asyncio.run(main())