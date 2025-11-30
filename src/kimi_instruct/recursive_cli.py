import asyncio, json, click
from .service import KimiInstructService
from .recursive_usaa import RecursiveUSAA

@click.command()
@click.option("--goal", required=True, help="Goal to pursue recursively")
@click.option("--context", default="{}", help="JSON context object")
@click.option("--dry-run", is_flag=True, help="Sandbox only, no real exec")
def recursive(goal, context, dry_run):
    base = KimiInstructService()
    wrapper = RecursiveUSAA(base)
    ctx = json.loads(context)
    if dry_run:
        ctx["dry_run_only"] = True
    result = asyncio.run(wrapper.run_recursive(goal, ctx))
    click.echo(json.dumps(result, indent=2))

if __name__ == "__main__":
    recursive()
