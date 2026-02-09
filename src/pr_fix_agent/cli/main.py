"""
CLI interface for PR Fix Agent.
"""

from __future__ import annotations

from typing import Optional
import typer
from rich.console import Console
from rich.table import Table

from pr_fix_agent.__version__ import __version__
from pr_fix_agent.core.config import get_settings
from pr_fix_agent.orchestrator import Orchestrator

app = typer.Typer(
    name="pr-fix-agent",
    help="Enterprise-grade AI-powered PR error fixing",
    add_completion=False,
)
console = Console()
settings = get_settings()


@app.command()
def version():
    """Show the version of PR Fix Agent."""
    console.print(f"PR Fix Agent [bold green]v{__version__}[/bold green]")


@app.command()
def health_check():
    """Run a health check on the system."""
    console.print("[bold blue]Running health check...[/bold blue]")
    table = Table(title="System Health")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_row("API", "Healthy")
    console.print(table)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    mode: Optional[str] = typer.Option(None, "--mode"),
    findings: Optional[str] = typer.Option(None, "--findings"),
    proposals: Optional[str] = typer.Option(None, "--proposals"),
    test_results: Optional[str] = typer.Option(None, "--test-results"),
    output: Optional[str] = typer.Option(None, "--output"),
    apply: bool = typer.Option(False, "--apply"),
):
    if ctx.invoked_subcommand is not None:
        return
    if mode is None:
        console.print(ctx.get_help())
        return
    if output is None:
        raise typer.Exit(code=1)

    orchestrator = Orchestrator()
    if mode == "reasoning":
        orchestrator.run_reasoning(findings, output)
    elif mode == "coding":
        orchestrator.run_coding(proposals, output, apply)
    elif mode == "generate-pr":
        orchestrator.generate_pr_body(proposals, test_results, output)
    else:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
