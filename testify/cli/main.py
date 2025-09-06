import typer

app = typer.Typer(
    help="testify - From spec to test. Generate Playwright/Cypress tests from acceptance criteria.",
    no_args_is_help=True,
)


@app.callback()
def main() -> None:
    """testify — From spec to test."""
    pass
