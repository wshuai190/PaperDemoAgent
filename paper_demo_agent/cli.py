"""CLI for Paper Demo Agent."""

import os
import sys
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table

console = Console()


@click.group()
@click.version_option(package_name="paper-demo-agent", prog_name="paper-demo-agent")
def cli():
    """Paper Demo Agent — turn any scientific paper into a live interactive demo."""
    pass


@cli.command()
@click.argument("source")
@click.option("--provider", "-p", default="anthropic", show_default=True,
              help="LLM provider (anthropic, openai, deepseek, qwen, gemini, minimax)")
@click.option("--model", "-m", default=None, help="Model override")
@click.option("--form", "-f", default=None,
              type=click.Choice(["app", "presentation", "page", "diagram"]),
              help="Demo category (app, presentation, page, diagram)")
@click.option("--subtype", "-s", default=None,
              help="Sub-type within category (e.g. gradio, streamlit, revealjs, beamer, pptx, project, readme, blog, mermaid, graphviz)")
@click.option("--type", "-t", "demo_type", default=None,
              type=click.Choice(["theoretical", "findings", "user_demo"]),
              help="Demo type override")
@click.option("--output", "-o", default=None, help="Output directory")
@click.option("--max-iter", default=25, show_default=True, help="Max agent iterations")
@click.option("--open/--no-open", "open_demo", default=True, show_default=True,
              help="Open demo in browser after generation")
@click.option("--api-key", default=None, envvar="LLM_API_KEY",
              help="API key override (or set PROVIDER_API_KEY env var)")
def demo(
    source: str,
    provider: str,
    model: Optional[str],
    form: Optional[str],
    subtype: Optional[str],
    demo_type: Optional[str],
    output: Optional[str],
    max_iter: int,
    open_demo: bool,
    api_key: Optional[str],
):
    """
    Generate a demo for a scientific paper.

    SOURCE can be:
    \b
    - arXiv ID:  1706.03762  or  arxiv:1706.03762
    - arXiv URL: https://arxiv.org/abs/1706.03762
    - Local PDF: /path/to/paper.pdf
    - Raw text:  "A paper about..."

    Categories & subtypes:
    \b
      app:          gradio (default), streamlit
      presentation: revealjs (default), beamer, pptx
      page:         project (default), readme, blog
      diagram:      mermaid (default), graphviz

    Examples:
    \b
        paper-demo-agent demo arxiv:1706.03762
        paper-demo-agent demo 1706.03762 --form app --subtype streamlit
        paper-demo-agent demo paper.pdf --form presentation --subtype beamer
        paper-demo-agent demo paper.pdf --form page --subtype readme
    """
    from paper_demo_agent.agent import PaperDemoAgent
    from paper_demo_agent.paper.models import CATEGORY_SUBTYPES

    # Validate subtype if given
    if subtype and not form:
        console.print("[red]Error:[/red] --subtype requires --form")
        sys.exit(1)
    if subtype and form:
        valid_subtypes = CATEGORY_SUBTYPES.get(form, [])
        if subtype not in valid_subtypes:
            console.print(
                f"[red]Error:[/red] Invalid subtype '{subtype}' for form '{form}'. "
                f"Valid subtypes: {', '.join(valid_subtypes)}"
            )
            sys.exit(1)

    # Normalize source (strip 'arxiv:' prefix)
    src = source.strip()
    if src.lower().startswith("arxiv:"):
        src = src[6:].strip()

    form_label = form or "auto"
    if subtype:
        form_label += f"/{subtype}"

    console.print(Panel.fit(
        f"[bold cyan]Paper Demo Agent[/bold cyan]\n"
        f"Source: [yellow]{src}[/yellow]\n"
        f"Provider: [green]{provider}[/green]"
        + (f" / {model}" if model else "")
        + f"\nForm: [blue]{form_label}[/blue]",
        title="🔬 Paper Demo Agent",
    ))

    progress_lines = []

    def on_progress(text: str):
        sys.stdout.write(text)
        sys.stdout.flush()
        progress_lines.append(text)

    try:
        agent = PaperDemoAgent(provider=provider, model=model, api_key=api_key)
        result = agent.run(
            source=src,
            output_dir=output,
            demo_form=form,
            demo_type=demo_type,
            demo_subtype=subtype,
            max_iter=max_iter,
            on_progress=on_progress,
        )
    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        sys.exit(1)

    if not result.success:
        console.print(f"\n[red]Generation failed:[/red] {result.error}")
        sys.exit(1)

    # Success summary
    console.print("\n")
    table = Table(title="✓ Demo Generated", show_header=True)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")
    table.add_row("Output Dir", result.output_dir)
    table.add_row("Main File", result.main_file)
    table.add_row("Form", result.demo_form)
    table.add_row("Type", result.demo_type)
    table.add_row("Run Command", result.run_command)
    console.print(table)

    if open_demo:
        console.print(f"\n[bold]Opening demo...[/bold]")
        from paper_demo_agent.generation.runner import DemoRunner
        try:
            runner = DemoRunner(result.output_dir, result.main_file)
            runner.run(open_browser=True)
        except Exception as e:
            console.print(f"[yellow]Could not auto-open demo:[/yellow] {e}")
            console.print(f"Run manually: [bold]{result.run_command}[/bold]")


@cli.command()
@click.option("--host", default="0.0.0.0", show_default=True, help="Host to bind to")
@click.option("--port", default=7860, show_default=True, help="Port to listen on")
@click.option("--share", is_flag=True, help="Create a public Gradio share link")
@click.option("--no-browser", is_flag=True, help="Don't auto-open browser")
@click.option("--auth", default=None, metavar="USER:PASS",
              help="Protect UI with username:password (e.g. admin:secret)")
def ui(host: str, port: int, share: bool, no_browser: bool, auth: Optional[str]):
    """Launch the local web interface (opens in browser)."""
    auth_tuple = None
    if auth:
        if ":" not in auth:
            console.print("[red]--auth must be in format user:password[/red]")
            sys.exit(1)
        user, password = auth.split(":", 1)
        auth_tuple = (user, password)
        console.print(f"[dim]Auth enabled for user: {user}[/dim]")

    console.print(Panel.fit(
        f"[bold cyan]Paper Demo Agent UI[/bold cyan]\n"
        f"Starting at [green]http://{host}:{port}[/green]"
        + (f"\n[dim]Protected with password auth[/dim]" if auth_tuple else ""),
        title="🔬 Paper Demo Agent",
    ))
    try:
        from paper_demo_agent.ui.app import launch
        launch(host=host, port=port, share=share, open_browser=not no_browser, auth=auth_tuple)
    except ImportError:
        console.print("[red]Gradio not installed.[/red] Run: pip install gradio")
        sys.exit(1)


@cli.command()
@click.option("--token", "-t", default=None, help="HuggingFace token (prompts if not given)")
def login(token: Optional[str]):
    """Log in to HuggingFace Hub (for gated models and datasets)."""
    if not token:
        token = click.prompt("HuggingFace token", hide_input=True)
    try:
        from huggingface_hub import login, whoami
        login(token=token, add_to_git_credential=False)
        info = whoami()
        username = info.get("name", "unknown")
        # Save it
        from paper_demo_agent.keys.manager import KeyManager
        KeyManager().set("HUGGINGFACE_TOKEN", token)
        console.print(f"[green]✓[/green] Logged in to HuggingFace as [bold]{username}[/bold]")
        console.print("[dim]Token saved to ~/.paper-demo-agent/config.json[/dim]")
    except Exception as e:
        console.print(f"[red]Login failed:[/red] {e}")
        sys.exit(1)


@cli.command()
def logout():
    """Log out of HuggingFace Hub."""
    try:
        from huggingface_hub import logout
        logout()
        console.print("[green]✓[/green] Logged out of HuggingFace")
    except Exception as e:
        console.print(f"[red]Logout error:[/red] {e}")


@cli.group()
def key():
    """Manage API keys."""
    pass


@key.command("set")
@click.argument("name")
@click.argument("value")
def key_set(name: str, value: str):
    """Set an API key.

    NAME: Key name (e.g. ANTHROPIC_API_KEY)
    VALUE: Key value
    """
    from paper_demo_agent.keys.manager import KeyManager
    km = KeyManager()
    try:
        km.set(name.upper(), value)
        console.print(f"[green]✓[/green] {name.upper()} saved to ~/.paper-demo-agent/config.json")
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@key.command("list")
def key_list():
    """List configured API keys."""
    from paper_demo_agent.keys.manager import KeyManager
    km = KeyManager()
    status = km.all_status()
    table = Table(title="API Key Status")
    table.add_column("Key", style="cyan")
    table.add_column("Status", style="white")
    for name, val in status.items():
        if val:
            table.add_row(name, f"[green]✓ Set[/green] ({val})")
        else:
            table.add_row(name, "[dim]Not set[/dim]")
    console.print(table)


@key.command("delete")
@click.argument("name")
def key_delete(name: str):
    """Delete a saved API key."""
    from paper_demo_agent.keys.manager import KeyManager
    km = KeyManager()
    km.delete(name.upper())
    console.print(f"[green]✓[/green] {name.upper()} deleted")


@cli.command()
def providers():
    """List all supported LLM providers."""
    from paper_demo_agent.providers.factory import PROVIDER_DEFAULTS
    table = Table(title="Supported Providers")
    table.add_column("Provider", style="cyan")
    table.add_column("Env Key", style="yellow")
    table.add_column("Default Model", style="white")
    table.add_column("Models", style="dim")
    for name, info in PROVIDER_DEFAULTS.items():
        table.add_row(
            name,
            info["key_env"],
            info["default_model"],
            ", ".join(info["models"][:3]) + ("..." if len(info["models"]) > 3 else ""),
        )
    console.print(table)


if __name__ == "__main__":
    cli()
