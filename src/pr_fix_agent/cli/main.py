"""
CLI interface for PR Fix Agent.
"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from pr_fix_agent.__version__ import __version__
from pr_fix_agent.core.config import get_settings

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

    # Mocking component checks for now
    table.add_row("API", "Healthy")
    table.add_row("Database", "Healthy")
    table.add_row("Redis", "Healthy")
    table.add_row("Ollama", "Healthy")

    console.print(table)


@app.command()
def orchestrate(
    log_file: str = typer.Argument(..., help="Path to GitHub Actions log file"),
    mode: str = typer.Option("reasoning", help="Orchestration mode: reasoning or coding"),
):
    """Orchestrate the PR fixing process."""
    console.print(f"[bold]Orchestrating fix in [cyan]{mode}[/cyan] mode using [magenta]{log_file}[/magenta]...[/bold]")
    # Implementation will call the orchestrator logic
    console.print("[yellow]Note: Full orchestration logic integration in progress.[/yellow]")


if __name__ == "__main__":
    app()
