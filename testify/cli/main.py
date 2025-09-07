from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from testify import __version__
from testify.cli.commands import generate

app = typer.Typer(
    help="testify - From spec to test. Generate Playwright/Cypress tests from acceptance criteria.",
    no_args_is_help=True,
)
console = Console()


@app.callback(invoke_without_command=True)
def main(
    version_flag: Annotated[
        bool,
        typer.Option(
            "--version",
            help="Show version and exit.",
            is_eager=True,
        ),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Enable verbose output.",
        ),
    ] = False,
) -> None:
    """CLI entry point."""
    if version_flag:
        console.print(f"testify v{__version__}")
        raise typer.Exit()

    if verbose:
        console.print("Verbose output enabled.")


app.command()(generate)


@app.command()
def init(
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            help="Overwrite an existing .testify.toml file.",
        ),
    ] = False,
) -> None:
    """Create a default .testify.toml config file."""
    config_path = ".testify.toml"
    content = "\n".join(
        [
            'framework = "playwright"',
            'output = "./tests"',
            'provider = "openai"',
            'model = "gpt-4o-mini"',
            "",
        ]
    )

    path = Path(config_path)
    if path.exists() and not force:
        console.print("[red].testify.toml already exists. Use --force to overwrite.[/red]")
        raise typer.Exit(code=1)

    path.write_text(content, encoding="utf-8")
    console.print(f"Created {config_path}")


@app.command()
def version() -> None:
    """Print version information."""
    console.print(f"testify v{__version__}")


@app.command("list-models")
def list_models() -> None:
    """List available LLM models."""
    table = Table(title="Available LLM models")
    table.add_column("Provider")
    table.add_column("Model")
    table.add_column("Notes")
    table.add_row("openai", "gpt-4o-mini", "Default")
    table.add_row("openai", "gpt-4o", "Higher capability")
    table.add_row("anthropic", "claude-3-5-sonnet-latest", "Optional dependency")
    console.print(table)
