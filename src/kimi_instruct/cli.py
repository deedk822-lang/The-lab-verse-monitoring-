"""
Kimi Instruct CLI Interface
Command-line interface for managing Kimi tasks and project status
"""
import asyncio
import json
import sys
from pathlib import Path
import click

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from kimi_instruct.service import KimiService

@click.group()
def cli():
    """Kimi Instruct - Hybrid AI Project Manager CLI"""
    pass

@cli.command()
@click.option('--output', type=click.Choice(['json', 'table']), default='table', help='Output format.')
def status(output):
    """Show project status"""
    # This is a simplified version. A real implementation would call the service.
    print("Fetching status...")
    # service = KimiService()
    # status = asyncio.run(service.get_status({}))
    # if output == 'json':
    #     click.echo(json.dumps(status, indent=2))
    # else:
    #     click.echo("Status in table format...")

@cli.command()
@click.option('--title', required=True, help='The title of the task.')
@click.option('--description', default="", help='A brief description of the task.')
@click.option('--priority', type=click.Choice(['low', 'medium', 'high', 'critical']), default='medium', help='The priority of the task.')
def create_task(title, description, priority):
    """Create a new task for Kimi to manage."""
    print(f"Creating task: {title}")
    # service = KimiService()
    # task = asyncio.run(service.create_task_logic(title, description, priority))
    # click.echo(f"Task created with ID: {task['id']}")

@cli.command()
@click.option('--goal', required=True, help='High-level USAA goal')
@click.option('--context', default='{}', help='JSON context string')
def usaa(goal: str, context: str):
    """Run USAA for a persistent goal."""
    # This is a simplified stub. A real implementation would initialize
    # the KimiInstruct class from core.py and run the goal.
    from kimi_instruct.core import KimiInstruct
    
    service = KimiInstruct()
    context_dict = json.loads(context)
    
    click.echo(f"Running USAA for goal: {goal}")
    
    # Since the service methods are async, we need an event loop
    async def run_goal():
        result = await service.run_usaa_goal(goal, context_dict)
        click.echo(json.dumps(result, indent=2))

    asyncio.run(run_goal())

if __name__ == '__main__':
    cli()