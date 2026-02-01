"""
Command-line interface for PR Fix Agent
"""

import asyncio
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ..agents.providers import AgentFactory
from ..api.main import create_app
from ..core.config import settings
from ..observability.metrics import CostTracker

app = typer.Typer()
console = Console()


@app.command()
def generate(
    prompt: str = typer.Argument(..., help="Text prompt for LLM generation"),
    provider: str = typer.Option("ollama", help="LLM provider to use"),
    model: Optional[str] = typer.Option(None, help="Specific model to use"),
    temperature: float = typer.Option(0.7, help="Generation temperature"),
    max_tokens: int = typer.Option(1000, help="Maximum tokens to generate"),
):
    """Generate text using specified LLM provider"""
    try:
        cost_tracker = CostTracker()
        agent = AgentFactory.create_agent(provider, cost_tracker)

        async def run_generation():
            async with agent:
                response = await agent.generate(
                    prompt,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return response

        response = asyncio.run(run_generation())

        console.print(f"\n[bold green]Response from {response.provider}/{response.model}:[/bold green]")
        console.print(response.content)
        console.print(f"\n[bold blue]Cost: ${response.cost.cost_usd:.4f}[/bold blue]")
        console.print(f"[dim]Input tokens: {response.cost.input_tokens}, Output tokens: {response.cost.output_tokens}[/dim]")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def providers():
    """List available LLM providers"""
    table = Table(title="LLM Providers")
    table.add_column("Provider", style="cyan")
    table.add_column("Available", style="green")
    table.add_column("Models", style="yellow")

    providers_info = {
        "ollama": {
            "available": True,
            "models": [settings.llm.ollama_model],
        },
        "openai": {
            "available": bool(settings.llm.openai_api_key),
            "models": ["gpt-4", "gpt-3.5-turbo"],
        },
        "cohere": {
            "available": bool(settings.llm.cohere_api_key),
            "models": ["command", "base"],
        },
        "huggingface": {
            "available": bool(settings.llm.huggingface_api_key),
            "models": [settings.llm.huggingface_model],
        },
    }

    for provider, info in providers_info.items():
        available = "✓" if info["available"] else "✗"
        models = ", ".join(info["models"])
        table.add_row(provider, available, models)

    console.print(table)


@app.command()
def cost():
    """Show current cost tracking information"""
    cost_tracker = CostTracker()

    table = Table(title="Cost Tracking")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="yellow")

    table.add_row("Daily Budget", f"${settings.llm.cost_budget_daily:.2f}")
    table.add_row("Costs Today", f"${cost_tracker.costs_today:.2f}")
    table.add_row("Remaining Budget", f"${max(0, settings.llm.cost_budget_daily - cost_tracker.costs_today):.2f}")
    table.add_row("Tracking Enabled", "✓" if settings.llm.enable_cost_tracking else "✗")

    console.print(table)


@app.command()
def serve(
    host: str = typer.Option(settings.api.api_host, help="Host to bind to"),
    port: int = typer.Option(settings.api.api_port, help="Port to bind to"),
    workers: int = typer.Option(settings.api.api_workers, help="Number of workers"),
):
    """Start the FastAPI server"""
    import uvicorn

    console.print(f"[bold green]Starting PR Fix Agent API server...[/bold green]")
    console.print(f"Host: {host}")
    console.print(f"Port: {port}")
    console.print(f"Workers: {workers}")

    uvicorn.run(
        "pr_fix_agent.api.main:create_app",
        host=host,
        port=port,
        workers=workers,
        factory=True,
        reload=settings.debug,
    )


@app.command()
def version():
    """Show version information"""
    console.print(f"[bold]PR Fix Agent[/bold] v0.1.0")
    console.print(f"Environment: {settings.environment}")
    console.print(f"Debug: {settings.debug}")


@app.callback()
def main():
    """PR Fix Agent - Enterprise-grade AI-powered PR error fixing system"""
    pass


if __name__ == "__main__":
    app()
