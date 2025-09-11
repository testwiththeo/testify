from enum import Enum
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from testify.generator.code_generator import CodeGenerator
from testify.llm import GeneratedTest, LLMClient, LLMConfig
from testify.parser import ScenarioInput, parse_input
from testify.writer import OutputWriter

console = Console()


class Framework(str, Enum):
    playwright = "playwright"
    cypress = "cypress"


class Language(str, Enum):
    typescript = "typescript"


def generate(
    input_text: Annotated[
        str | None,
        typer.Argument(
            metavar="INPUT",
            help="Input text, file, or directory. Defaults to stdin in later phases.",
        ),
    ] = None,
    framework: Annotated[
        Framework,
        typer.Option(
            "--framework",
            "-f",
            help="Target framework: playwright or cypress.",
        ),
    ] = Framework.playwright,
    output_dir: Annotated[
        str,
        typer.Option(
            "--output",
            "-o",
            help="Output directory for generated tests.",
        ),
    ] = "./tests",
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            "-d",
            help="Preview output without writing files.",
        ),
    ] = False,
    template: Annotated[
        str | None,
        typer.Option(
            "--template",
            "-t",
            help="Path to a custom Jinja2 template.",
        ),
    ] = None,
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            help="Overwrite existing files.",
        ),
    ] = False,
    no_page_objects: Annotated[
        bool,
        typer.Option(
            "--no-page-objects",
            help="Skip page object generation.",
        ),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Enable detailed logging.",
        ),
    ] = False,
    language: Annotated[
        Language,
        typer.Option(
            "--language",
            help="Output language. TypeScript only in v1.",
        ),
    ] = Language.typescript,
) -> None:
    """Generate tests from acceptance criteria."""
    console.print("Parsed generate parameters:")
    console.print(f"input: {input_text or '<stdin>'}")
    console.print(f"framework: {framework.value}")
    console.print(f"output: {output_dir}")
    console.print(f"dry_run: {dry_run}")
    console.print(f"template: {template or '<built-in>'}")
    console.print(f"force: {force}")
    console.print(f"page_objects: {not no_page_objects}")
    console.print(f"verbose: {verbose}")
    console.print(f"language: {language.value}")

    scenarios = parse_input(input_text)
    if not scenarios:
        console.print("[red]No scenarios found[/red]")
        raise typer.Exit(code=1)

    if dry_run:
        _preview_dry_run(scenarios)
        console.print(
            f"[green]Processed {len(scenarios)} scenario(s). Generated 0 file(s).[/green]"
        )
        return

    llm_client = LLMClient(config=LLMConfig.from_env())
    generator = CodeGenerator(template_dir=_template_directory(template))
    rendered_files, failures = _generate_files(
        scenarios=scenarios,
        framework=framework.value,
        llm_client=llm_client,
        generator=generator,
        include_page_objects=not no_page_objects,
        verbose=verbose,
    )

    for scenario, error in failures:
        console.print(f"[yellow]⚠ Failed to generate test for: {scenario.text}[/yellow]")
        if verbose:
            console.print(f"[yellow]{error}[/yellow]")

    if not rendered_files:
        console.print("[red]Failed to generate any tests[/red]")
        raise typer.Exit(code=1)

    writer = OutputWriter(console=console)
    try:
        written = writer.write(
            rendered_files,
            Path(output_dir),
            force=force,
            dry_run=False,
        )
    except PermissionError:
        raise typer.Exit(code=1) from None

    console.print(
        f"[green]Processed {len(scenarios)} scenario(s). Generated {len(written)} file(s).[/green]"
    )


def _preview_dry_run(scenarios: list[ScenarioInput]) -> None:
    for scenario in scenarios:
        console.print(f"[blue]? Would generate test for: {scenario.text}[/blue]")


def _template_directory(template: str | None) -> Path | None:
    if template is None:
        return None

    template_path = Path(template)
    if template_path.suffix:
        return template_path.parent
    return template_path


def _generate_files(
    scenarios: list[ScenarioInput],
    framework: str,
    llm_client: LLMClient,
    generator: CodeGenerator,
    include_page_objects: bool,
    verbose: bool,
) -> tuple[dict[str, str], list[tuple[ScenarioInput, Exception]]]:
    rendered_files: dict[str, str] = {}
    failures: list[tuple[ScenarioInput, Exception]] = []

    with console.status("[bold green]Generating tests..."):
        for scenario in scenarios:
            try:
                generated = llm_client.generate_test(scenario, framework)
                _prepare_generated_test(generated, framework, include_page_objects)
                rendered_files.update(generator.generate(generated))
            except Exception as error:
                failures.append((scenario, error))

    return rendered_files, failures


def _prepare_generated_test(
    generated: GeneratedTest,
    framework: str,
    include_page_objects: bool,
) -> None:
    generated.framework = framework
    if not include_page_objects:
        generated.page_objects = None
