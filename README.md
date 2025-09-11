# testify

From spec to test.

testify is a Python CLI that turns natural language acceptance criteria into editable Playwright or Cypress TypeScript tests. It reads inline text, stdin, spec files, or directories, asks an LLM for structured test data, renders framework-specific code with Jinja2 templates, and writes files safely without overwriting existing work unless asked.

## Status

testify is alpha software. Generated tests should be reviewed before committing.

## Quick Start

```bash
pip install testify
export TESTIFY_LLM_API_KEY="sk-..."

testify generate "User logs in with valid credentials, sees dashboard"
```

By default, testify generates Playwright TypeScript tests in `./tests`.

For local development from source:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Usage

Generate from inline text:

```bash
testify generate "User logs in with valid credentials" --framework playwright
```

Generate from a file:

```bash
testify generate spec.txt --output ./tests
```

Generate from a directory:

```bash
testify generate specs/ --framework cypress --output ./e2e
```

Preview without calling the LLM or writing files:

```bash
testify generate specs/ --dry-run
```

Use a custom template directory:

```bash
testify generate spec.txt --template ./templates
```

Overwrite existing generated files:

```bash
testify generate spec.txt --force
```

Skip page object generation:

```bash
testify generate spec.txt --no-page-objects
```

## Framework Examples

Playwright:

```bash
testify generate "User logs in and sees the dashboard" --framework playwright
```

Expected output uses `test`, `expect`, async `page`, and Playwright locators.

Cypress:

```bash
testify generate "User logs in and sees the dashboard" --framework cypress
```

Expected output uses `describe`, `it`, `cy.visit`, `cy.get`, and `cy.url().should`.

## Input Formats

Plain text files use one scenario per non-empty line:

```text
User logs in with valid credentials
User logs out
```

Markdown lists are supported:

```markdown
- User logs in with valid credentials
* User logs out
```

Directory mode recursively reads `.txt`, `.md`, and `.spec` files.

## Configuration

Environment variables:

| Variable | Default | Description |
| --- | --- | --- |
| `TESTIFY_LLM_PROVIDER` | `openai` | LLM provider. |
| `TESTIFY_LLM_MODEL` | `gpt-4o-mini` | Model used for generation. |
| `TESTIFY_LLM_API_KEY` | unset | Preferred API key variable. |
| `OPENAI_API_KEY` | unset | Fallback API key for OpenAI. |
| `TESTIFY_DEFAULT_FRAMEWORK` | `playwright` | Planned default framework override. |
| `TESTIFY_OUTPUT_DIR` | `./tests` | Planned default output directory override. |

Create a starter project config:

```bash
testify init
```

## Development

Install development dependencies:

```bash
pip install -e ".[dev]"
```

Run checks:

```bash
pytest --cov=testify
ruff check testify/
mypy testify/
```

Install pre-commit hooks:

```bash
pre-commit install
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, coding standards, testing, and pull request guidance.

## License

MIT. See [LICENSE](LICENSE).
