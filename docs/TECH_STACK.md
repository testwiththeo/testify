# testify — Tech Stack & Setup Guide

## 1. Technology Choices

### Core Language: Python 3.10+

**Why:** Best ecosystem for LLM tooling, strong typing via Pydantic, rich CLI libraries, and wide adoption for developer tooling.

### CLI Framework: Typer

**Why:** Built on Click, type-driven, automatic help text generation, minimal boilerplate. Industry standard for Python CLIs.

### Output Formatting: Rich

**Why:** Colored terminal output, syntax highlighting, tables, progress bars. Makes the CLI feel polished and professional.

### LLM Client: OpenAI SDK + Anthropic SDK

**Why:** Most widely supported LLM APIs. Abstraction layer so users can choose providers.

### Structured Output: Pydantic v2

**Why:** Type-safe parsing of LLM JSON responses, validation, serialization. Essential for reliable code generation.

### Templating: Jinja2

**Why:** Industry standard Python templating. Easy to write, easy for users to customize. No need for AST manipulation in v1.

### Retry / Resilience: Tenacity

**Why:** Simple declarative retry with exponential backoff. Battle-tested for API calls.

### Testing: pytest + VCR.py

**Why:** pytest is standard. VCR.py records LLM API responses so tests don't hit real APIs in CI.

### Package Management: uv (or Poetry)

**Why:** Fast dependency resolution, deterministic lock files, clean build process.

## 2. Full Dependency List

```toml
# pyproject.toml
[project]
name = "testify"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "typer>=0.12.0",
    "rich>=13.0.0",
    "pydantic>=2.0.0",
    "openai>=1.0.0",
    "jinja2>=3.1.0",
    "tenacity>=8.0.0",
    "pyyaml>=6.0",       # config file parsing
    "tomli>=2.0.0",      # TOML config parsing (Python 3.10)
]

[project.optional-dependencies]
anthropic = ["anthropic>=0.30.0"]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=5.0.0",
    "vcrpy>=6.0.0",
    "ruff>=0.5.0",
    "mypy>=1.0.0",
    "pre-commit>=3.0.0",
]
```

## 3. Project Structure

```
testify/
├── pyproject.toml
├── README.md
├── LICENSE
├── .gitignore
├── .pre-commit-config.yaml
├── docs/
│   ├── PRD.md
│   ├── SRS.md
│   ├── ARCHITECTURE.md
│   ├── TECH_STACK.md
│   └── IMPLEMENTATION_PLAN.md
├── tests/
│   ├── conftest.py
│   ├── test_cli.py
│   ├── test_input_parser.py
│   ├── test_llm_client.py
│   ├── test_code_generator.py
│   └── test_output_writer.py
├── testify/
│   ├── __init__.py
│   ├── __main__.py           # python -m testify entry
│   ├── cli/
│   │   ├── __init__.py
│   │   ├── main.py           # Typer app
│   │   └── commands.py       # Command implementations
│   ├── parser/
│   │   ├── __init__.py
│   │   └── input_parser.py   # Input reading + parsing
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── client.py         # LLM API client
│   │   ├── config.py         # LLM configuration
│   │   └── schemas.py        # Pydantic models for LLM output
│   ├── generator/
│   │   ├── __init__.py
│   │   ├── code_generator.py # Template rendering
│   │   └── templates/        # Jinja2 templates
│   │       ├── playwright_spec.jinja2
│   │       ├── cypress_spec.jinja2
│   │       ├── playwright_page.jinja2
│   │       └── cypress_page.jinja2
│   ├── writer/
│   │   ├── __init__.py
│   │   └── output_writer.py  # File output management
│   └── config/
│       ├── __init__.py
│       └── settings.py       # Configuration loading
```

## 4. Setup Instructions

```bash
# Clone
git clone https://github.com/yourusername/testify.git
cd testify

# Install with uv (recommended)
uv venv
uv sync

# Or with pip
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Set your API key
export TESTIFY_LLM_API_KEY="sk-..."

# Run
testify generate "User logs in with valid credentials"

# Run tests
pytest

# Type check
mypy testify/

# Lint
ruff check testify/
```

## 5. CI/CD (GitHub Actions)

```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.10"
      - run: pip install -e ".[dev]"
      - run: pytest --cov=testify
      - run: mypy testify/
      - run: ruff check testify/
```
