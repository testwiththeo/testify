# testify — Implementation Plan for AI Agent

## Overview

This document is written for an AI coding agent. It breaks down testify into 7 sequential phases. Each phase produces working, testable code. Complete phases in order.

## Phase 1: Project Scaffolding

**Goal:** Set up the Python project structure, build system, and CLI skeleton.

**Files to create:**

### 1.1 `pyproject.toml`

```toml
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "testify"
version = "0.1.0"
description = "From spec to test. Generate Playwright/Cypress tests from acceptance criteria."
requires-python = ">=3.10"
dependencies = [
    "typer>=0.12.0",
    "rich>=13.0.0",
    "pydantic>=2.0.0",
    "openai>=1.0.0",
    "jinja2>=3.1.0",
    "tenacity>=8.0.0",
    "pyyaml>=6.0",
    "tomli>=2.0.0",
]

[project.scripts]
testify = "testify.cli.main:app"

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=5.0.0",
    "vcrpy>=6.0.0",
    "ruff>=0.5.0",
    "mypy>=1.0.0",
]
```

### 1.2 `testify/__init__.py`
Empty file.

### 1.3 `testify/__main__.py`
```python
from testify.cli.main import app
app()
```

### 1.4 `testify/cli/__init__.py`
Empty file.

### 1.5 `testify/cli/main.py`
Create a basic Typer app with a `generate` command that takes `input: str` as argument and prints it back.

**Test:** Run `testify --help` and verify output.
**Test:** Run `testify generate "hello"` and verify it prints the input.

### 1.6 `testify/cli/commands.py`
Define the `generate` function signature with all parameters. For now, just print parameters and return.

Parameters:
- `input_text: Optional[str] = None` (argument)
- `framework: str = "playwright"` (option, choices: playwright, cypress)
- `output_dir: str = "./tests"` (option, short: -o)
- `dry_run: bool = False` (option, flag, short: -d)
- `template: Optional[str] = None` (option, short: -t)
- `force: bool = False` (option, flag)
- `no_page_objects: bool = False` (option, flag)
- `verbose: bool = False` (option, flag, short: -v)

### 1.7 `testify/parser/__init__.py`
Empty file.

### 1.8 `testify/llm/__init__.py`
Empty file.

### 1.9 `testify/generator/__init__.py`
Empty file.

### 1.10 `testify/writer/__init__.py`
Empty file.

### 1.11 `testify/config/__init__.py`
Empty file.

### 1.12 `tests/conftest.py`
Empty file for now.

### 1.13 `tests/test_cli.py`
```python
from typer.testing import CliRunner
from testify.cli.main import app

runner = CliRunner()

def test_help_succeeds():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "generate" in result.output

def test_generate_with_input():
    result = runner.invoke(app, ["generate", "User logs in"])
    assert result.exit_code == 0

def test_generate_with_framework_flag():
    result = runner.invoke(app, ["generate", "User logs in", "--framework", "cypress"])
    assert result.exit_code == 0

def test_generate_invalid_framework():
    result = runner.invoke(app, ["generate", "User logs in", "--framework", "selenium"])
    assert result.exit_code != 0

def test_generate_dry_run():
    result = runner.invoke(app, ["generate", "User logs in", "--dry-run"])
    assert result.exit_code == 0
```

**Acceptance criteria for Phase 1:**
- `pip install -e ".[dev]"` succeeds
- `testify --help` shows all commands and options
- `testify generate "hello"` runs without error
- All CLI tests pass with `pytest`

---

## Phase 2: Input Parser

**Goal:** Parse input from stdin, string argument, file, and directory into structured ScenarioInput objects.

**Files to create/modify:**

### 2.1 `testify/parser/input_parser.py`

Implement these functions:

**`parse_input(source: Optional[str]) -> List[ScenarioInput]`**
- If source is None: read from stdin
- If source is a file path that exists: parse_file
- If source is a directory path that exists: parse_directory
- Otherwise: treat as raw text string

**`parse_stdin() -> List[ScenarioInput]`**
- Read all lines from sys.stdin
- Filter empty lines
- Create ScenarioInput for each non-empty line

**`parse_text(text: str, source: str = "argument") -> List[ScenarioInput]`**
- Split by newlines
- Filter empty lines
- Detect markdown list items (`- item`) and strip the prefix
- Return list of ScenarioInput

**`parse_file(path: str) -> List[ScenarioInput]`**
- Read file content
- Detect format: if `.md`, parse as markdown list; otherwise split by lines
- Return list with source = file path

**`parse_directory(path: str) -> List[ScenarioInput]`**
- Walk directory recursively
- Collect files matching `*.txt`, `*.md`, `*.spec`
- Parse each file and flatten into one list

**Pydantic model (in parser/input_parser.py):**
```python
class ScenarioInput(BaseModel):
    text: str
    source: str
    line_number: Optional[int] = None
```

**Tests (`tests/test_input_parser.py`):**
- Test parsing a plain text string
- Test parsing stdin (mock sys.stdin)
- Test parsing a file (use tmp_path fixture)
- Test parsing a directory with multiple spec files
- Test empty input handling
- Test markdown list input stripping

**Acceptance criteria for Phase 2:**
- `parse_text("User logs in\nUser sees dashboard")` returns 2 ScenarioInputs
- `parse_text("- User logs in\n- User sees dashboard")` returns 2 ScenarioInputs with clean text
- `parse_input(None)` reads from stdin
- `parse_input("nonexistent.txt")` treats as string, not file
- All parser tests pass

---

## Phase 3: LLM Client

**Goal:** Send parsed input to an LLM and receive structured test data.

**Files to create:**

### 3.1 `testify/llm/schemas.py`

Pydantic models for structured LLM output:

```python
from pydantic import BaseModel
from typing import Optional, List, Dict

class TestStep(BaseModel):
    action: str
    selector: Optional[str] = None
    value: Optional[str] = None
    assertion: Optional[str] = None

class TestScenario(BaseModel):
    name: str
    description: str
    steps: List[TestStep]
    assertions: List[str]
    page: Optional[str] = None
    test_data: Optional[Dict[str, str]] = None

class PageObject(BaseModel):
    name: str
    selectors: Dict[str, str]

class GeneratedTest(BaseModel):
    filename: str
    framework: str
    language: str = "typescript"
    describe_block: str
    scenarios: List[TestScenario]
    imports: List[str]
    page_objects: Optional[List[PageObject]] = None
```

### 3.2 `testify/llm/config.py`

```python
from pydantic import BaseModel
from typing import Optional

class LLMConfig(BaseModel):
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    api_key: Optional[str] = None
    temperature: float = 0.2
    max_tokens: int = 2000
    timeout: int = 30
    max_retries: int = 3
```

Load config from environment variables:
- `TESTIFY_LLM_PROVIDER` → provider
- `TESTIFY_LLM_MODEL` → model
- `TESTIFY_LLM_API_KEY` → api_key (fallback: `OPENAI_API_KEY`)

### 3.3 `testify/llm/client.py`

Implement an LLM client with provider abstraction:

**`LLMClient` class:**

```python
class LLMClient:
    def __init__(self, config: Optional[LLMConfig] = None):
        # Load config from env if not provided
        ...

    def generate_test(self, scenario: ScenarioInput, framework: str) -> GeneratedTest:
        # 1. Build system prompt
        # 2. Build user prompt with scenario + framework
        # 3. Call LLM with retry
        # 4. Parse JSON response into GeneratedTest
        # 5. Return GeneratedTest or raise ParseError
```

**Prompt design:**

System prompt:
```
You are an expert QA engineer who writes clean, idiomatic {framework} tests.
Given an acceptance criterion, generate a complete test with proper assertions.
Return ONLY valid JSON matching the provided schema. No explanations, no markdown.
```

User prompt:
```
Framework: {framework}
Acceptance Criterion: {scenario.text}

Generate test code with:
1. A descriptive test name
2. Step-by-step actions with selectors
3. Clear assertions
4. Page objects if a page/screen is mentioned

Use data-testid selectors like: [data-testid="element-name"]
```

**Retry logic (using tenacity):**
- Retry 3 times
- Exponential backoff: 2s, 4s, 8s
- Only retry on: timeout, connection error, invalid JSON
- Don't retry on: auth error, bad request

**Tests (`tests/test_llm_client.py`):**
- Mock OpenAI API response and verify parsing
- Test retry on timeout
- Test retry on invalid JSON
- Test auth error is not retried
- Test config loading from environment variables

**Note:** Use VCR.py to record real API responses for deterministic testing. Include a cassette file for tests to pass without API calls.

### 3.4 `testify/llm/__init__.py`
Export `LLMClient`, `LLMConfig`, `GeneratedTest`.

**Acceptance criteria for Phase 3:**
- `LLMClient().generate_test(ScenarioInput(text="User logs in"), "playwright")` returns a valid GeneratedTest
- Invalid JSON from LLM triggers retry
- Auth error raises clear "set your API key" message
- All LLM client tests pass

---

## Phase 4: Code Generator

**Goal:** Convert GeneratedTest data into actual code files using templates.

**Files to create:**

### 4.1 `testify/generator/templates/playwright_spec.jinja2`

```jinja2
import {{ test.imports | join(', ') }} from '@playwright/test';
{% if test.page_objects %}
{% for po in test.page_objects %}
import { {{ po.name }} } from '../pages/{{ po.name | lower }}.page';
{% endfor %}
{% endif %}

test.describe('{{ test.describe_block }}', () => {
{% for scenario in test.scenarios %}
  test('{{ scenario.name }}', async ({ page }) => {
{% if scenario.page %}
    const {{ scenario.page | lower }} = new {{ scenario.page }}(page);
    await {{ scenario.page | lower }}.goto();
{% endif %}
{% for step in scenario.steps %}
{% if step.selector and step.value %}
    await page.locator('{{ step.selector }}').fill('{{ step.value }}');
{% elif step.selector and step.action == 'click' %}
    await page.locator('{{ step.selector }}').click();
{% elif step.selector %}
    await page.locator('{{ step.selector }}').fill('{{ step.value }}');
{% elif step.action == 'navigate' %}
    await page.goto('{{ step.value }}');
{% endif %}
{% endfor %}
{% for assertion in scenario.assertions %}
    {{ assertion }}
{% endfor %}
  });
{% endfor %}
});
```

### 4.2 `testify/generator/templates/cypress_spec.jinja2`

Similar structure with Cypress syntax (`cy.visit`, `cy.get`, `cy.url().should`, etc.)

### 4.3 `testify/generator/templates/playwright_page.jinja2`

```jinja2
export class {{ page.name }} {
  constructor(public page: Page) {}

{% for selector_name, selector_value in page.selectors.items() %}
  readonly {{ selector_name }} = '{{ selector_value }}';
{% endfor %}

  async goto() {
    await this.page.goto('/{{ page.name | lower }}');
  }
{% for method in page.methods %}
  async {{ method.name }}({{ method.params }}) {
    {{ method.body }}
  }
{% endfor %}
}
```

### 4.4 `testify/generator/templates/cypress_page.jinja2`

Cypress page object using Cypress commands pattern.

### 4.5 `testify/generator/code_generator.py`

```python
class CodeGenerator:
    def __init__(self, template_dir: Optional[Path] = None):
        # Load Jinja2 environment
        # If custom template_dir provided, add to loader path
        ...

    def generate(self, test: GeneratedTest) -> Dict[str, str]:
        # Returns dict of {relative_path: rendered_code}
        # Select template based on test.framework
        # Render spec template
        # Render page object templates if applicable
        ...

    def _render_template(self, template_name: str, context: dict) -> str:
        ...
```

**Tests (`tests/test_code_generator.py`):**
- Generate Playwright test from a GeneratedTest → verify imports, describe block, assertions
- Generate Cypress test → verify uses cy.* syntax
- Generate with page objects → verify page object file is created
- Generate with custom template → verify custom template is used
- Verify generated code is syntactically valid TypeScript (optional: run through prettier)

**Acceptance criteria for Phase 4:**
- `CodeGenerator().generate(test)` returns dict with correct file paths
- Playwright output uses `test`, `expect` from playwright
- Cypress output uses `cy.get`, `cy.visit`, `cy.url`
- Page objects are generated when test has page_objects
- Custom templates override built-in templates

---

## Phase 5: Output Writer

**Goal:** Write generated code to disk safely with progress feedback.

**Files to create:**

### 5.1 `testify/writer/output_writer.py`

```python
from pathlib import Path
from typing import Dict, List
from rich.console import Console

class OutputWriter:
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()

    def write(
        self,
        files: Dict[str, str],
        output_dir: Path,
        force: bool = False,
        dry_run: bool = False,
    ) -> List[Path]:
        """
        Write generated files to disk.
        
        Args:
            files: Dict mapping relative paths to code strings
            output_dir: Base output directory
            force: Overwrite existing files
            dry_run: Preview without writing
        
        Returns:
            List of written file paths
        """
        ...

    def _write_file(self, path: Path, content: str, force: bool) -> Path:
        # Atomic write: write to .tmp, then rename
        ...

    def _preview(self, files: Dict[str, str]) -> None:
        # Print file paths and preview first 10 lines
        ...
```

**Safety guarantees:**
- Check if file exists before writing
- If exists and not force, skip with warning
- Print: `✓ Created tests/login.spec.ts` in green
- Print: `⚠ Skipped tests/logout.spec.ts (use --force to overwrite)` in yellow
- Dry run prints: `? Would create tests/login.spec.ts` in blue

**Tests (`tests/test_output_writer.py`):**
- Write files to temp directory → verify files exist
- Write with existing file (no force) → verify file not overwritten
- Write with existing file (force) → verify file overwritten
- Dry run → verify no files created
- Verify directory structure is created

### 5.2 Update `testify/writer/__init__.py`
Export `OutputWriter`.

**Acceptance criteria for Phase 5:**
- `OutputWriter().write({"tests/test.spec.ts": "code"}, Path("/tmp/out"))` creates the file
- `OutputWriter().write(..., dry_run=True)` doesn't create files
- Existing files are not overwritten without `--force`
- Rich console output shows colors

---

## Phase 6: Integration & CLI Completion

**Goal:** Wire all modules together in the CLI command and provide a working end-to-end tool.

**Files to modify:**

### 6.1 `testify/cli/commands.py`

Implement the full `generate` command:

```python
def generate(
    input_text: Optional[str] = typer.Argument(None, help="Acceptance criteria text, file path, or directory"),
    framework: str = typer.Option("playwright", "--framework", "-f", help="Target test framework"),
    output_dir: str = typer.Option("./tests", "--output", "-o", help="Output directory"),
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Preview output without writing"),
    template: Optional[str] = typer.Option(None, "--template", "-t", help="Custom template file path"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing files"),
    no_page_objects: bool = typer.Option(False, "--no-page-objects", help="Skip page object generation"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
):
    """Generate test files from acceptance criteria."""
    
    # 1. Parse input
    scenarios = parse_input(input_text)
    if not scenarios:
        console.print("[red]No scenarios found in input.[/red]")
        raise typer.Exit(1)
    
    # 2. Initialize LLM client
    llm_config = LLMConfig.from_env()
    llm_client = LLMClient(config=llm_config)
    
    # 3. Generate tests (with progress spinner)
    all_files = {}
    with console.status("[bold green]Generating tests...") as status:
        for scenario in scenarios:
            try:
                generated = llm_client.generate_test(scenario, framework)
                generator = CodeGenerator(template_dir=Path(template) if template else None)
                files = generator.generate(generated)
                all_files.update(files)
            except Exception as e:
                console.print(f"[red]Failed to generate test for: {scenario.text}[/red]")
                if verbose:
                    console.print(f"[red]{e}[/red]")
    
    # 4. Write output
    writer = OutputWriter()
    written = writer.write(all_files, Path(output_dir), force=force, dry_run=dry_run)
    
    # 5. Print summary
    console.print(f"\n[green]Done! Generated {len(written)} file(s).[/green]")
```

### 6.2 `testify/cli/main.py`

Add `init`, `version`, `list-models` commands:

```python
app = typer.Typer()

@app.callback()
def main():
    """testify — From spec to test. Generate Playwright/Cypress tests from acceptance criteria."""
    pass

app.command()(generate)

@app.command()
def init():
    """Create a .testify.toml configuration file."""
    config_path = Path(".testify.toml")
    if config_path.exists():
        console.print("[yellow].testify.toml already exists.[/yellow]")
        raise typer.Exit()
    config_path.write_text(DEFAULT_CONFIG)
    console.print("[green]Created .testify.toml[/green]")

@app.command()
def version():
    """Print version information."""
    from testify import __version__
    console.print(f"testify v{__version__}")

@app.command(name="list-models")
def list_models():
    """List available LLM models."""
    models = {
        "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
        "anthropic": ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022"],
    }
    for provider, provider_models in models.items():
        console.print(f"[bold]{provider}:[/bold]")
        for m in provider_models:
            console.print(f"  - {m}")
```

### 6.3 End-to-end test

Create `tests/test_integration.py`:

```python
def test_end_to_end(tmp_path, monkeypatch):
    """Run the full pipeline with mocked LLM."""
    # Mock LLM response
    monkeypatch.setenv("TESTIFY_LLM_API_KEY", "sk-test")
    
    # Write a spec file
    spec_file = tmp_path / "spec.txt"
    spec_file.write_text("User logs in with valid credentials, sees dashboard")
    
    # Run CLI
    result = runner.invoke(app, [
        "generate", str(spec_file),
        "--output", str(tmp_path / "tests"),
    ])
    
    # Verify output
    assert result.exit_code == 0
    assert (tmp_path / "tests" / "login.spec.ts").exists()
```

**Acceptance criteria for Phase 6:**
- `testify generate "User logs in" --dry-run` shows preview without writing files
- `testify generate spec.txt` reads file and generates tests
- `testify init` creates config file
- `testify version` prints version
- `testify list-models` prints available models
- Integration tests pass

---

## Phase 7: Polish & Production Readiness

**Goal:** Documentation, error handling, edge cases, packaging.

### 7.1 Error handling pass
Review every module for unhandled exceptions. Add try/except with user-friendly messages.

### 7.2 Logging
Replace print statements with proper logging. Support `--verbose` flag.

### 7.3 Pre-commit hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.5.0
    hooks:
      - id: ruff
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.10.0
    hooks:
      - id: mypy
```

### 7.4 Complete `.gitignore`
```
__pycache__/
*.pyc
.venv/
dist/
*.egg-info/
.testify.toml
.env
*.ts  # generated test files
```

### 7.5 README.md
Full README with:
- What is testify?
- Quick start
- Usage examples
- Configuration reference
- Contributing guide
- License

### 7.6 GitHub templates
- `.github/ISSUE_TEMPLATE/bug_report.md`
- `.github/ISSUE_TEMPLATE/feature_request.md`
- `CONTRIBUTING.md`

### 7.7 PyPI packaging
```bash
pip install build
python -m build
twine upload dist/*
```

**Acceptance criteria for Phase 7:**
- `ruff check testify/` passes with zero warnings
- `mypy testify/` passes with zero errors
- `pytest --cov=testify` shows > 80% coverage
- `pip install testify` installs successfully (test in fresh venv)
- `testify generate "User logs in"` runs end-to-end with a real API key

---

## Summary of Build Order

| Phase | What | Depends On | Estimated Time |
|-------|------|------------|----------------|
| 1 | Project scaffolding | Nothing | 30 min |
| 2 | Input parser | Phase 1 | 1 hour |
| 3 | LLM client | Phase 2 | 2 hours |
| 4 | Code generator | Phase 3 | 1.5 hours |
| 5 | Output writer | Phase 4 | 1 hour |
| 6 | Integration & CLI | Phases 2-5 | 2 hours |
| 7 | Polish & release | Phase 6 | 2 hours |

**Total: ~10 hours of development time for an AI agent.**

Each phase has tests that must pass before moving to the next phase. Do not skip phases. Do not move forward if tests fail.
