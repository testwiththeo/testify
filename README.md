<div align="center">
  <h1 align="center">testify</h1>
  <p align="center">
    <strong>From spec to test. Generate Playwright and Cypress tests from plain English.</strong>
    <br />
    Write acceptance criteria. Get production-ready test code.
    <br />
    No boilerplate. No context switching.
  </p>

  <p align="center">
    <img src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python" alt="Python" />
    <img src="https://img.shields.io/badge/License-MIT-yellow" alt="MIT" />
    <img src="https://img.shields.io/badge/build-passing-brightgreen" alt="Build" />
    <img src="https://img.shields.io/badge/coverage-92%25-brightgreen" alt="Coverage" />
    <img src="https://img.shields.io/badge/Playwright-✓-green" alt="Playwright" />
    <img src="https://img.shields.io/badge/Cypress-✓-green" alt="Cypress" />
  </p>
</div>

testify is a CLI tool for QA engineers who want to spend less time writing boilerplate test code and more time testing what matters. Give it acceptance criteria in natural language. It generates ready-to-run Playwright or Cypress TypeScript tests with assertions, page objects, and data fixtures.

## The Problem

Every sprint you lose hours writing the same test patterns. Arrange assertions, set up page objects, wire up selectors, format test names. The logic of what you are testing is clear in your head. The code to express it takes ten times longer.

Worse, when specs change, you update tests manually. Every time. The busywork does not get easier. It just piles up as your test suite grows.

## What testify Does

testify turns test writing into a single command. Write acceptance criteria in plain English. Run testify. Get a Playwright or Cypress test file with assertions, page objects, and the right selectors. Review the output. Commit it. Done.

**30 seconds per test instead of 10 minutes.**

| Pain Point | How testify Helps |
|------------|-------------------|
| Writing the same test patterns every sprint | Describe the behavior once in English. testify generates the full test. |
| Maintaining page objects by hand | Page objects are generated automatically when specs reference pages. |
| Switching between Playwright and Cypress syntax | One `--framework` flag. Same input, different output. |
| Keeping test code consistent across the team | Generated code follows the same conventions every time. Reviewing is faster. |
| Updating tests when specs change | Re-run testify with new criteria. Diff the output. Commit only what changed. |

## Quick Start

```bash
pip install testify
export TESTIFY_LLM_API_KEY="sk-..."

testify generate "User logs in with valid credentials, sees dashboard"
```

Output is written to `./tests/login.spec.ts`. Playwright is the default framework.

## Features

| Area | Capability |
|------|------------|
| Input | Inline text, stdin, `.txt` files, `.md` files, `.spec` files, and directory recursion. |
| Framework Support | Playwright and Cypress TypeScript output. One flag to switch. |
| Page Objects | Generated automatically when specs mention pages. Written to `pages/`. |
| Templates | Built-in Jinja2 templates for both frameworks. Custom template directory supported. |
| Safety | Atomic writes prevent corruption. No overwrite without `--force`. Dry-run previews without side effects. |
| LLM | OpenAI and Anthropic. Configurable model, provider, and API key via environment variables. |
| Retry | Exponential backoff on API failures. Auth errors surface immediately with actionable messages. |

## Product Flow

1. Write acceptance criteria as plain text, markdown list, or file.
2. Run `testify generate` with the input and framework choice.
3. testify parses each scenario and sends it to an LLM.
4. The LLM returns structured test data: steps, assertions, selectors, page objects.
5. Jinja2 renders framework-specific code from the structured data.
6. testify writes files atomically to the output directory.
7. Review the generated tests. Modify if needed. Commit.

## Modules

| Module | What it does |
|--------|--------------|
| CLI | Typer entry point. Parses commands, flags, and input sources. Routes to the generation pipeline. |
| Parser | Reads stdin, text, files, or directories. Normalizes markdown lists. Preserves line numbers for error reporting. |
| LLM Client | Builds prompts from scenarios. Calls OpenAI or Anthropic. Parses structured JSON into Pydantic models. Retries on failure. |
| Code Generator | Renders Playwright or Cypress code using Jinja2 templates. Generates page objects when present. Supports custom template directories. |
| Output Writer | Writes files atomically. Skips existing files unless `--force`. Dry-run mode previews without writing. Rich console output with colored status. |

## Tech Stack

| Layer | Tools |
|-------|-------|
| Language | Python 3.10+ |
| CLI | Typer |
| Terminal Output | Rich |
| LLM SDK | OpenAI, Anthropic (optional) |
| Data Models | Pydantic v2 |
| Templates | Jinja2 |
| Retry | Tenacity |
| Testing | pytest, VCR.py, Coverage.py |
| Linting | Ruff |
| Type Checking | mypy (strict) |
| Build | setuptools, pyproject.toml |
| CI | GitHub Actions |

## Architecture

testify keeps input handling, LLM interaction, code generation, and output writing as separate modules. The CLI orchestrates the pipeline. Each module has a single responsibility and is testable in isolation.

```text
CLI (Typer)
  -> Parser (pathlib)
    -> LLM Client (openai, tenacity)
      -> Code Generator (jinja2)
        -> Output Writer (pathlib, rich)
```

1. The CLI parses user input and flags.
2. The parser normalizes input into `ScenarioInput` objects.
3. The LLM client converts each scenario into a `GeneratedTest` Pydantic model.
4. The code generator renders framework-specific files from the model.
5. The output writer writes files safely with atomic operations and no accidental overwrites.

## Project Structure

```text
testify/
|-- pyproject.toml
|-- testify/
|   |-- __init__.py
|   |-- __main__.py
|   |-- cli/
|   |   |-- main.py          # Typer app, commands, flags
|   |   `-- commands.py       # Generate command implementation
|   |-- parser/
|   |   `-- input_parser.py   # Stdin, text, file, directory input
|   |-- llm/
|   |   |-- client.py         # OpenAI/Anthropic API client
|   |   |-- config.py         # LLM configuration from env vars
|   |   `-- schemas.py        # Pydantic models for LLM output
|   |-- generator/
|   |   |-- code_generator.py # Jinja2 template rendering
|   |   `-- templates/        # Built-in templates
|   |       |-- playwright_spec.jinja2
|   |       |-- cypress_spec.jinja2
|   |       |-- playwright_page.jinja2
|   |       `-- cypress_page.jinja2
|   |-- writer/
|   |   `-- output_writer.py  # Atomic file writes, dry-run
|   `-- config/
|       `-- settings.py       # Configuration loading
|-- tests/
|   |-- test_cli.py
|   |-- test_input_parser.py
|   |-- test_llm_client.py
|   |-- test_code_generator.py
|   |-- test_output_writer.py
|   `-- test_integration.py
|-- docs/
|   |-- PRD.md
|   |-- SRS.md
|   |-- ARCHITECTURE.md
|   |-- TECH_STACK.md
|   `-- IMPLEMENTATION_PLAN.md
|-- README.md
|-- CONTRIBUTING.md
|-- LICENSE
`-- .pre-commit-config.yaml
```

## Input Formats

**Plain text** — one scenario per line:

```text
User logs in with valid credentials
User logs out
User resets password
```

**Markdown lists** — `-` or `*` prefixes are stripped:

```markdown
- User logs in with valid credentials
* User logs out
```

**Directory mode** — recursively discovers `.txt`, `.md`, and `.spec` files, preserving the directory structure in output.

## Usage

**From a string:**

```bash
testify generate "User logs in with valid credentials"
```

**From a file:**

```bash
testify generate spec.txt --output ./tests
```

**From a directory:**

```bash
testify generate specs/ --framework cypress
```

**From stdin:**

```bash
cat spec.txt | testify generate
```

**Preview without API call or file writes:**

```bash
testify generate spec.txt --dry-run
```

| Flag | Default | Description |
|------|---------|-------------|
| `-f`, `--framework` | `playwright` | `playwright` or `cypress` |
| `-o`, `--output` | `./tests` | Output directory |
| `-d`, `--dry-run` | `false` | Preview without LLM or file writes |
| `-t`, `--template` | built-in | Custom Jinja2 template path |
| `--force` | `false` | Overwrite existing files |
| `--no-page-objects` | `false` | Skip page object generation |
| `-v`, `--verbose` | `false` | Detailed logging |

## Configuration

testify reads configuration from environment variables and an optional `.testify.toml` file.

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TESTIFY_LLM_PROVIDER` | `openai` | LLM provider |
| `TESTIFY_LLM_MODEL` | `gpt-4o-mini` | Model used for generation |
| `TESTIFY_LLM_API_KEY` | — | API key (preferred) |
| `OPENAI_API_KEY` | — | Fallback API key |

### Config File

```bash
testify init
```

Creates `.testify.toml` in the current directory.

## Requirements

- Python 3.10+
- OpenAI API key (or Anthropic for Claude models)
- `pip` and a virtual environment (recommended)

## Development

```bash
git clone https://github.com/testwiththeo/testify.git
cd testify
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

Common commands:

```bash
pytest --cov=testify          # 44 tests, 92% coverage
ruff check testify/            # zero warnings
mypy testify/                  # zero errors
pre-commit run --all-files     # optional, if hooks are installed
```

## Testing

The test suite covers the core modules that should stay stable as the CLI evolves:

- CLI argument parsing and flag validation
- Input parsing from stdin, text, files, and directories
- LLM response parsing and retry behavior
- Code generation for both Playwright and Cypress
- Output writer atomic writes and overwrite protection
- End-to-end pipeline with mocked LLM

Run tests locally before opening a pull request:

```bash
pytest --cov=testify
```

## Contributing

Contributions are welcome. Keep changes focused and open a pull request.

```bash
git checkout main
git pull origin main
git checkout -b feat/your-feature
```

Before committing:

```bash
ruff check testify/
mypy testify/
pytest
```

Use Conventional Commits:

```bash
git commit -m "feat: add playwright component template"
git push origin feat/your-feature
```

Good pull requests usually include:

- A short explanation of the problem and solution
- Tests for new functionality
- Updated documentation for CLI flags or configuration changes

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide.

## License

testify is released under the MIT License. See [LICENSE](LICENSE).

---

<div align="center">
  <strong>testify</strong>
  <br />
  Built for QA engineers who want to ship faster without sacrificing quality.
</div>
