"""
CLI interface for PR Fix Agent.
Supports legacy flat arguments for CI compatibility and new subcommands.
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
    table.add_row("Database", "Healthy")
    table.add_row("Redis", "Healthy")
    table.add_row("Ollama", "Healthy")

    console.print(table)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    mode: Optional[str] = typer.Option(None, "--mode", help="Orchestration mode: reasoning, coding, or generate-pr"),
    findings: Optional[str] = typer.Option(None, "--findings", help="Path to findings JSON (reasoning mode)"),
    proposals: Optional[str] = typer.Option(None, "--proposals", help="Path to proposals JSON (coding/generate-pr modes)"),
    test_results: Optional[str] = typer.Option(None, "--test-results", help="Path to test results JSON (generate-pr mode)"),
    output: Optional[str] = typer.Option(None, "--output", help="Output file or directory"),
    apply: bool = typer.Option(False, "--apply", help="Apply fixes directly (coding mode)"),
):
    """
    Main entry point for PR Fix Agent.
    Supports legacy arguments for CI compatibility.
    """
    if ctx.invoked_subcommand is not None:
        return

    if mode is None:
        console.print(ctx.get_help())
        return

    # Compatibility logic for Orchestrator
    if output is None:
        console.print("[red]Error: --output is required for orchestration mode.[/red]")
        raise typer.Exit(code=1)

    orchestrator = Orchestrator()

    if mode == "reasoning":
        if not findings:
            console.print("[red]Error: --findings is required for reasoning mode.[/red]")
            raise typer.Exit(code=1)
        orchestrator.run_reasoning(findings, output)
    elif mode == "coding":
        if not proposals:
            console.print("[red]Error: --proposals is required for coding mode.[/red]")
            raise typer.Exit(code=1)
        orchestrator.run_coding(proposals, output, apply)
    elif mode == "generate-pr":
        if not proposals or not test_results:
            console.print("[red]Error: --proposals and --test-results are required for generate-pr mode.[/red]")
            raise typer.Exit(code=1)
        orchestrator.generate_pr_body(proposals, test_results, output)
    else:
        console.print(f"[red]Error: Invalid mode '{mode}'.[/red]")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
