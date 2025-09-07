from enum import Enum
from typing import Optional

import typer
from rich.console import Console

console = Console()


class Framework(str, Enum):
    playwright = "playwright"
    cypress = "cypress"


class Language(str, Enum):
    typescript = "typescript"


def generate(
    input_text: Optional[str] = typer.Argument(
        None,
        metavar="INPUT",
        help="Input text, file, or directory. Defaults to stdin.",
    ),
    framework: Framework = typer.Option(
        Framework.playwright,
        "--framework", "-f",
        help="Target framework: playwright or cypress.",
    ),
    output_dir: str = typer.Option(
        "./tests",
        "--output", "-o",
        help="Output directory for generated tests.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run", "-d",
        help="Preview output without writing files.",
    ),
    template: Optional[str] = typer.Option(
        None,
        "--template", "-t",
        help="Path to a custom Jinja2 template.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Overwrite existing files.",
    ),
    no_page_objects: bool = typer.Option(
        False,
        "--no-page-objects",
        help="Skip page object generation.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Enable detailed logging.",
    ),
    language: Language = typer.Option(
        Language.typescript,
        "--language",
        help="Output language. TypeScript only in v1.",
    ),
) -> None:
    """Generate tests from acceptance criteria."""
    console.print("Parsed generate parameters:")
    console.print(f"  input         : {input_text or '<stdin>'}")
    console.print(f"  framework     : {framework.value}")
    console.print(f"  output        : {output_dir}")
    console.print(f"  dry_run       : {dry_run}")
    console.print(f"  template      : {template or '<built-in>'}")
    console.print(f"  force         : {force}")
    console.print(f"  page_objects  : {not no_page_objects}")
    console.print(f"  verbose       : {verbose}")
    console.print(f"  language      : {language.value}")
