 feature/ml-anomaly-detection
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
=======
"""
Kimi Instruct CLI Interface
Command-line interface for managing Kimi tasks and project status
"""
import asyncio
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from kimi_instruct.core import KimiInstruct, TaskPriority, TaskStatus

class KimiCLI:
    """Command-line interface for Kimi Instruct"""

    def __init__(self):
        self.kimi = None

    async def initialize(self):
        """Initialize Kimi instance"""
        self.kimi = KimiInstruct()

    async def status_command(self, args):
        """Show project status"""
        status = await self.kimi.get_status_report()

        if args.output == 'json':
            print(json.dumps(status, indent=2, default=str))
            return

        # Pretty print status
        print("\n🎯 KIMI PROJECT STATUS")
        print("=" * 50)

        # Progress info
        task_summary = status['task_summary']
        print(f"Progress: {task_summary['completion_percentage']:.1f}%")
        print(f"Tasks: {task_summary['completed']}/{task_summary['total']} completed")
        print(f"Risk Level: {status['risk_level'].upper()}")

        # Context info
        context = status['project_context']
        print(f"Budget Remaining: ${context['budget_remaining']:.2f}")
        print(f"Timeline Status: {context['timeline_status']}")

        # Critical issues
        if status['critical_issues']:
            print("\n⚠️  CRITICAL ISSUES:")
            for issue in status['critical_issues']:
                print(f"  • {issue['title']}: {issue['reason']}")

        # Next actions
        if status['next_actions']:
            print("\n📝 NEXT ACTIONS:")
            for action in status['next_actions']:
                print(f"  • [{action['priority'].upper()}] {action['description']}")

        print()
    
    async def task_command(self, args):
        """Create and execute a task"""
        if not args.title:
            print("Error: --title required for task command")
            return

        # Parse priority
        try:
            priority = TaskPriority(args.priority)
        except ValueError:
            print(f"Error: Invalid priority '{args.priority}'. Use: low, medium, high, critical")
            return

        # Create task
        task = await self.kimi.create_task(
            title=args.title,
            description=args.description or "",
            priority=priority,
            metadata={"cli_created": True}
        )

        print(f"✅ Created task: {task.id}")
        print(f"   Title: {task.title}")
        print(f"   Priority: {priority.value}")
        print(f"   Status: {task.status.value}")

        # Execute if requested
        if args.execute:
            print("\n🔄 Executing task...")
            success = await self.kimi.execute_task(task.id)
            if success:
                print("✅ Task executed successfully")
            else:
                print("❌ Task execution failed")
    
    async def list_tasks_command(self, args):
        """List all tasks"""
        if args.output == 'json':
            tasks_data = []
            for task in self.kimi.tasks.values():
                tasks_data.append({
                    "id": task.id,
                    "title": task.title,
                    "priority": task.priority.value,
                    "status": task.status.value,
                    "created_at": task.created_at.isoformat()
                })
            print(json.dumps({"tasks": tasks_data}, indent=2))
            return

        # Pretty print tasks
        if not self.kimi.tasks:
            print("No tasks found.")
            return

        print("\n📋 TASKS")
        print("=" * 60)

        # Group by status
        by_status = {}
        for task in self.kimi.tasks.values():
            status = task.status.value
            if status not in by_status:
                by_status[status] = []
            by_status[status].append(task)

        for status, tasks in by_status.items():
            print(f"\n{status.upper()} ({len(tasks)}):")
            for task in tasks:
                priority_icon = {
                    "critical": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "low": "🟢"
                }.get(task.priority.value, "⚪")

                print(f"  {priority_icon} {task.title}")
                print(f"     ID: {task.id}")
                print(f"     Created: {task.created_at.strftime('%Y-%m-%d %H:%M')}")
                if task.description:
                    print(f"     Description: {task.description}")

        print()
    
    async def optimize_command(self, args):
        """Run project optimization"""
        # Create optimization task
        task = await self.kimi.create_task(
            title="Optimize project costs and performance",
            description="Analyze current project status and recommend optimizations",
            priority=TaskPriority.MEDIUM,
            metadata={"cli_optimization": True}
        )

        print(f"🔄 Running optimization...")

        # Execute optimization
        success = await self.kimi.execute_task(task.id)

        if success:
            result = task.metadata.get('result', {})
            if args.output == 'json':
                print(json.dumps(result, indent=2, default=str))
            else:
                print("\n💰 OPTIMIZATION RESULTS")
                print("=" * 40)
                print(f"Potential Savings: ${result.get('savings', 0):.2f}")
                print(f"Optimizations Found: {result.get('optimizations', 0)}")
                print(f"ROI Projection: {result.get('roi', 0) * 100:.1f}%")
        else:
            print("❌ Optimization failed")

    async def checkin_command(self, args):
        """Perform human checkin"""
        print("\n👋 HUMAN CHECKIN")
        print("=" * 30)

        # Get current status
        status = await self.kimi.get_status_report()

        print(f"Current Progress: {status['task_summary']['completion_percentage']:.1f}%")
        print(f"Risk Level: {status['risk_level'].upper()}")
        print(f"Budget Remaining: ${status['project_context']['budget_remaining']:.2f}")

        # Update checkin time
        self.kimi.context.last_human_checkin = datetime.now()

        # Log checkin
        self.kimi.decision_history.append({
            "type": "cli_checkin",
            "data": {"timestamp": datetime.now().isoformat()},
            "timestamp": datetime.now().isoformat()
        })

        print("\n✅ Checkin completed")
        print(f"Next checkin due: {self.kimi.context.last_human_checkin.strftime('%Y-%m-%d %H:%M')}")

    async def report_command(self, args):
        """Generate project report"""
        status = await self.kimi.get_status_report()

        if args.output == 'json':
            print(json.dumps(status, indent=2, default=str))
            return

        # Generate comprehensive report
        print("\n📊 KIMI PROJECT REPORT")
        print("=" * 60)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Executive Summary
        print("\n📈 EXECUTIVE SUMMARY")
        print("-" * 30)
        task_summary = status['task_summary']
        context = status['project_context']

        print(f"Overall Progress: {task_summary['completion_percentage']:.1f}%")
        print(f"Total Tasks: {task_summary['total']}")
        print(f"Completed: {task_summary['completed']}")
        print(f"In Progress: {task_summary['in_progress']}")
        print(f"Blocked: {task_summary['blocked']}")

        # Financial Status
        print("\n💰 FINANCIAL STATUS")
        print("-" * 25)
        initial_budget = 50000.0  # From config
        spent = initial_budget - context['budget_remaining']
        print(f"Budget Remaining: ${context['budget_remaining']:.2f}")
        print(f"Amount Spent: ${spent:.2f}")
        print(f"Budget Utilization: {(spent / initial_budget) * 100:.1f}%")

        # Risk Assessment
        print("\n⚠️ RISK ASSESSMENT")
        print("-" * 25)
        print(f"Current Risk Level: {status['risk_level'].upper()}")
        print(f"Risk Score: {context['metrics'].get('risk_score', 0):.2f}")
        print(f"Human Interventions: {context['metrics'].get('human_intervention_count', 0)}")

        # Critical Issues
        if status['critical_issues']:
            print("\n🔴 CRITICAL ISSUES")
            print("-" * 25)
            for issue in status['critical_issues']:
                print(f"• {issue['title']}")
                print(f"  Reason: {issue['reason']}")

        # Recommendations
        if status['next_actions']:
            print("\n💡 RECOMMENDATIONS")
            print("-" * 25)
            for action in status['next_actions']:
                priority_icon = {
                    "critical": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "low": "🟢"
                }.get(action['priority'], "⚪")
                print(f"{priority_icon} {action['description']}")

        print()

async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Kimi Instruct - Hybrid AI Project Manager CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s status                              # Show project status
  %(prog)s task --title "Deploy service"        # Create a task
  %(prog)s task --title "Fix bug" --execute     # Create and execute task
  %(prog)s list                               # List all tasks
  %(prog)s optimize                           # Run optimization
  %(prog)s checkin                            # Perform human checkin
  %(prog)s report                             # Generate project report
        """
    )

    parser.add_argument(
        "command",
        choices=['status', 'task', 'list', 'optimize', 'checkin', 'report'],
        help="Command to execute"
    )

    # Task creation options
    parser.add_argument("--title", type=str, help="Task title")
    parser.add_argument("--description", type=str, help="Task description")
    parser.add_argument(
        "--priority",
        choices=['low', 'medium', 'high', 'critical'],
        default='medium',
        help="Task priority"
    )
    parser.add_argument(
        "--execute",
        action='store_true',
        help="Execute task immediately after creation"
    )

    # Output options
    parser.add_argument(
        "--output",
        choices=['json', 'table'],
        default='table',
        help="Output format"
    )

    args = parser.parse_args()

    # Initialize CLI
    cli = KimiCLI()
    await cli.initialize()

    # Route to appropriate command
    try:
        if args.command == 'status':
            await cli.status_command(args)
        elif args.command == 'task':
            await cli.task_command(args)
        elif args.command == 'list':
            await cli.list_tasks_command(args)
        elif args.command == 'optimize':
            await cli.optimize_command(args)
        elif args.command == 'checkin':
            await cli.checkin_command(args)
        elif args.command == 'report':
            await cli.report_command(args)

    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
 main
