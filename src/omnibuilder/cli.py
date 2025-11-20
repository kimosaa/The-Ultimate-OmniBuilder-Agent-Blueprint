"""
OmniBuilder CLI Interface

Command-line interface for interacting with the OmniBuilder agent.
"""

import asyncio
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn

from omnibuilder import __version__
from omnibuilder.agent import OmniBuilderAgent
from omnibuilder.config import Config

app = typer.Typer(
    name="omnibuilder",
    help="OmniBuilder - Autonomous Developer Agent",
    add_completion=False
)

console = Console()


def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        console.print(f"OmniBuilder v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None, "--version", "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version"
    )
) -> None:
    """OmniBuilder - Autonomous Developer Agent"""
    pass


@app.command()
def run(
    goal: str = typer.Argument(..., help="The goal or task to execute"),
    config: Optional[str] = typer.Option(
        None, "--config", "-c",
        help="Path to config file"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-V",
        help="Verbose output"
    )
) -> None:
    """Execute a goal autonomously."""
    async def _run():
        # Load config
        cfg = Config.load(config)
        cfg.verbose = verbose

        # Create agent
        agent = OmniBuilderAgent(cfg)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Initializing agent...", total=None)

            await agent.initialize()

            progress.update(task, description=f"Executing: {goal}")

            result = await agent.run(goal)

            progress.update(task, description="Complete!")

        # Display result
        console.print()
        console.print(Panel(
            Markdown(result),
            title="Result",
            border_style="green"
        ))

        await agent.stop()

    asyncio.run(_run())


@app.command()
def chat(
    config: Optional[str] = typer.Option(
        None, "--config", "-c",
        help="Path to config file"
    )
) -> None:
    """Start interactive chat with the agent."""
    async def _chat():
        cfg = Config.load(config)
        agent = OmniBuilderAgent(cfg)

        console.print(Panel(
            "[bold]OmniBuilder Interactive Mode[/bold]\n\n"
            "Type your messages to interact with the agent.\n"
            "Commands: /quit, /status, /clear, /help",
            border_style="blue"
        ))

        await agent.initialize()

        while True:
            try:
                # Get user input
                user_input = console.input("[bold cyan]You:[/bold cyan] ")

                if not user_input.strip():
                    continue

                # Handle commands
                if user_input.startswith("/"):
                    cmd = user_input.lower().strip()

                    if cmd in ["/quit", "/exit", "/q"]:
                        console.print("[dim]Goodbye![/dim]")
                        break

                    elif cmd == "/status":
                        state = agent.get_state()
                        console.print(f"Running: {state['is_running']}")
                        console.print(f"Current task: {state['current_task']}")
                        console.print(f"Messages: {state['message_count']}")
                        continue

                    elif cmd == "/clear":
                        agent.stm.clear_context()
                        console.print("[dim]Context cleared[/dim]")
                        continue

                    elif cmd == "/help":
                        console.print("""
[bold]Commands:[/bold]
  /quit, /exit, /q  - Exit the chat
  /status           - Show agent status
  /clear            - Clear context
  /help             - Show this help
                        """)
                        continue

                    else:
                        console.print(f"[red]Unknown command: {cmd}[/red]")
                        continue

                # Process message
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                    transient=True
                ) as progress:
                    progress.add_task("Thinking...", total=None)
                    response = await agent.chat(user_input)

                console.print(f"[bold green]Agent:[/bold green] {response}\n")

            except KeyboardInterrupt:
                console.print("\n[dim]Use /quit to exit[/dim]")
            except EOFError:
                break

        await agent.stop()

    asyncio.run(_chat())


@app.command()
def init(
    path: str = typer.Argument(".", help="Project directory"),
    force: bool = typer.Option(
        False, "--force", "-f",
        help="Overwrite existing config"
    )
) -> None:
    """Initialize OmniBuilder configuration in a project."""
    import os
    from pathlib import Path

    project_dir = Path(path).resolve()
    config_dir = project_dir / ".omnibuilder"

    if config_dir.exists() and not force:
        console.print(f"[yellow]Config already exists at {config_dir}[/yellow]")
        console.print("Use --force to overwrite")
        raise typer.Exit(1)

    # Create directories
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "memory").mkdir(exist_ok=True)
    (config_dir / "logs").mkdir(exist_ok=True)

    # Create default config
    config = Config()
    config.save(str(config_dir / "config.yaml"))

    console.print(f"[green]Initialized OmniBuilder in {project_dir}[/green]")
    console.print(f"Config file: {config_dir / 'config.yaml'}")


@app.command()
def index(
    path: str = typer.Argument(".", help="Directory to index")
) -> None:
    """Index a codebase for the agent."""
    from omnibuilder.environment.codebase import CodebaseContextProvider

    provider = CodebaseContextProvider(path)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task(f"Indexing {path}...", total=None)
        index = provider.index_codebase()
        progress.update(task, description="Complete!")

    console.print(f"[green]Indexed {len(index.files)} files[/green]")
    console.print(f"Found {len(index.symbols)} symbols")


@app.command()
def plan(
    goal: str = typer.Argument(..., help="Goal to plan for"),
    config: Optional[str] = typer.Option(
        None, "--config", "-c",
        help="Path to config file"
    )
) -> None:
    """Create an execution plan for a goal."""
    async def _plan():
        cfg = Config.load(config)
        agent = OmniBuilderAgent(cfg)
        await agent.initialize()

        plan = await agent.planner.create_execution_plan(goal)

        console.print(Panel(
            f"[bold]Plan for:[/bold] {goal}\n"
            f"[bold]ID:[/bold] {plan.id}\n"
            f"[bold]Estimated time:[/bold] {plan.estimated_duration}s",
            title="Execution Plan",
            border_style="blue"
        ))

        console.print("\n[bold]Steps:[/bold]")
        for i, step in enumerate(plan.steps, 1):
            console.print(f"  {i}. {step.description}")
            if step.tool_name:
                console.print(f"     [dim]Tool: {step.tool_name}[/dim]")

        await agent.stop()

    asyncio.run(_plan())


@app.command()
def tools() -> None:
    """List available tools."""
    from omnibuilder.core.selector import ToolSelector

    selector = ToolSelector()
    all_tools = selector.list_tools()

    console.print(Panel(
        f"[bold]{len(all_tools)} tools available[/bold]",
        title="OmniBuilder Tools",
        border_style="blue"
    ))

    # Group by category
    by_category = {}
    for tool in all_tools:
        cat = tool.category.value
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(tool)

    for category, tools in sorted(by_category.items()):
        console.print(f"\n[bold]{category}:[/bold]")
        for tool in tools:
            risk_color = {
                "low": "green",
                "medium": "yellow",
                "high": "red",
                "critical": "red bold"
            }.get(tool.risk_level.value, "white")

            console.print(
                f"  - {tool.name}: {tool.description} "
                f"[{risk_color}]({tool.risk_level.value})[/{risk_color}]"
            )


def main() -> None:
    """Entry point."""
    app()


if __name__ == "__main__":
    main()
