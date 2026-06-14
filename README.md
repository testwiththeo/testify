# testify

> From spec to test. Generate Playwright and Cypress tests from plain English acceptance criteria.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](pyproject.toml)

testify is a CLI tool for QA engineers who want to spend less time writing boilerplate test code and more time testing what matters. Give it acceptance criteria in natural language — it generates ready-to-run Playwright or Cypress TypeScript tests with assertions, page objects, and data fixtures.

```bash
pip install testify
export TESTIFY_LLM_API_KEY="sk-..."

echo "User logs in with valid credentials, sees dashboard" | testify generate
```

---

## Table of Contents

- [Quick Start](#quick-start)
- [Usage](#usage)
  - [Input Sources](#input-sources)
  - [Options](#options)
  - [Framework Examples](#framework-examples)
- [How It Works](#how-it-works)
- [Input Formats](#input-formats)
- [Configuration](#configuration)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

---

## Quick Start

```bash
# Install
pip install testify

# Set your API key
export TESTIFY_LLM_API_KEY="sk-..."

# Generate a test from plain English
testify generate "User logs in with valid credentials, sees dashboard"
```

Output is written to `./tests/login.spec.ts`. Playwright is the default framework.

---

## Usage

### Input Sources

**From a string:**

```bash
testify generate "User logs in with valid credentials"
```

**From a file:**

```bash
testify generate spec.txt --output ./tests
```

**From a directory** (recursively reads `.txt`, `.md`, `.spec` files):

```bash
testify generate specs/ --framework cypress
```

**From stdin:**

```bash
cat spec.txt | testify generate
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `-f`, `--framework` | `playwright` | Target framework: `playwright` or `cypress` |
| `-o`, `--output` | `./tests` | Output directory |
| `-d`, `--dry-run` | `false` | Preview output without calling the LLM or writing files |
| `-t`, `--template` | built-in | Path to custom Jinja2 templates |
| `--force` | `false` | Overwrite existing files |
| `--no-page-objects` | `false` | Skip page object generation |
| `-v`, `--verbose` | `false` | Enable detailed logging |

### Framework Examples

**Playwright:**

```bash
testify generate "User logs in and sees the dashboard" --framework playwright
```

Generated output uses `test` / `expect`, async `page`, and Playwright locators with `data-testid` selectors.

**Cypress:**

```bash
testify generate "User logs in and sees the dashboard" --framework cypress
```

Generated output uses `describe` / `it`, `cy.visit`, `cy.get`, and `cy.url().should`.

**Preview (no API call, no files written):**

```bash
testify generate spec.txt --dry-run --verbose
```

---

## How It Works

```
┌──────────┐    ┌──────────────┐    ┌────────────┐    ┌────────────────┐    ┌──────────────┐
│  Input   │───▶│    Parser    │───▶│ LLM Client │───▶│    Generator   │───▶│    Writer    │
│ stdin    │    │ split lines  │    │ OpenAI     │    │ Jinja2 render  │    │ atomic write │
│ file     │    │ strip mkdn   │    │ structured │    │ framework      │    │ dry-run      │
│ string   │    │ normalize    │    │ output     │    │ specific       │    │ safe create  │
│ dir      │    │              │    │            │    │                │    │              │
└──────────┘    └──────────────┘    └────────────┘    └────────────────┘    └──────────────┘
```

1. **Input** — acceptance criteria from stdin, a string argument, a file, or a directory
2. **Parser** — splits input into scenarios, normalizes markdown lists, preserves line numbers
3. **LLM Client** — sends each scenario to an LLM, receives structured test data as Pydantic models
4. **Generator** — renders Playwright or Cypress code using Jinja2 templates, including page objects
5. **Writer** — writes files atomically, skips existing unless `--force`, supports dry-run preview

---

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

**Directory mode** — recursively discovers `.txt`, `.md`, and `.spec` files, maintaining directory structure in output.

---

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

Creates `.testify.toml` in the current directory with default values.

---

## Development

```bash
# Clone and install
git clone https://github.com/testwiththeo/testify.git
cd testify
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Run checks
pytest --cov=testify          # 44 tests, 92% coverage
ruff check testify/            # zero warnings
mypy testify/                  # zero errors

# Install pre-commit hooks (optional)
pre-commit install
```

---

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for:

- Development environment setup
- Coding standards (ruff, mypy, pytest)
- Pull request process
- Issue templates

---

## License

MIT. See [LICENSE](LICENSE).
