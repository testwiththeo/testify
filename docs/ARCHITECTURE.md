# testify — System Architecture

## 1. High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                        User                             │
│  testify generate "User logs in, sees dashboard"        │
└────────────────────┬────────────────────────────────────┘
                     │ CLI command
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   CLI Layer (Typer)                      │
│  - Parse arguments                                       │
│  - Read input (stdin, file, string, directory)           │
│  - Validate options                                      │
│  - Route to generator                                    │
└────────────────────┬────────────────────────────────────┘
                     │ Structured input
                     ▼
┌─────────────────────────────────────────────────────────┐
│                Input Parser Module                       │
│  - Split input into individual scenarios                 │
│  - Normalize format (text, markdown)                     │
│  - Extract metadata (page names, test data hints)        │
└────────────────────┬────────────────────────────────────┘
                     │ List[ScenarioInput]
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  LLM Client Module                       │
│  - Build prompt from scenario + framework                │
│  - Send to LLM provider (OpenAI, Anthropic, etc.)        │
│  - Parse structured JSON response (Pydantic)             │
│  - Retry on failure (3x, exponential backoff)            │
└────────────────────┬────────────────────────────────────┘
                     │ GeneratedTest (Pydantic model)
                     ▼
┌─────────────────────────────────────────────────────────┐
│               Code Generator Module                      │
│  - Select template (built-in or custom)                  │
│  - Render Jinja2 template with GeneratedTest data        │
│  - Format output with Prettier (if available)            │
│  - Generate page objects if applicable                   │
└────────────────────┬────────────────────────────────────┘
                     │ Rendered code strings
                     ▼
┌─────────────────────────────────────────────────────────┐
│                Output Writer Module                      │
│  - Check for existing files (no overwrite without force) │
│  - Create directory structure                            │
│  - Write files to disk                                   │
│  - Print summary of created files                        │
└─────────────────────────────────────────────────────────┘
```

## 2. Module Breakdown

### 2.1 CLI Layer (`cli/main.py`)

**Responsibility:** Entry point, argument parsing, routing.

**Dependencies:** `typer`, `rich`

**Key functions:**
- `generate(input, framework, output, dry_run, template, force, no_page_objects)`
- `init()` — create default config file
- `version()` — print version
- `list_models()` — print supported LLM models

### 2.2 Input Parser (`parser/input_parser.py`)

**Responsibility:** Convert raw user input into structured scenarios.

**Dependencies:** `pathlib`

**Key functions:**
- `parse_text(text: str) -> List[ScenarioInput]` — split by newlines, filter empty
- `parse_file(path: Path) -> List[ScenarioInput]` — read and parse file
- `parse_directory(path: Path) -> List[ScenarioInput]` — walk directory, parse all spec files
- `parse_stdin() -> List[ScenarioInput]` — read from stdin

**ScenarioInput model:**
```python
class ScenarioInput(BaseModel):
    text: str
    source: str  # file path or "stdin" or "argument"
    line_number: Optional[int]
```

### 2.3 LLM Client (`llm/client.py`)

**Responsibility:** Interface with LLM provider, return structured output.

**Dependencies:** `openai` (or `anthropic`), `pydantic`, `tenacity`

**Key functions:**
- `generate_test(input: ScenarioInput, framework: str, config: LLMConfig) -> GeneratedTest`

**LLMConfig:**
```python
class LLMConfig(BaseModel):
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    api_key: Optional[str] = None
    temperature: float = 0.2
    max_tokens: int = 2000
    timeout: int = 30
    max_retries: int = 3
```

**Prompt template (pseudo):**
```
You are an expert QA engineer writing {framework} tests.

Given this acceptance criterion:
"{scenario_text}"

Generate a complete test file following these rules:
1. Use idiomatic {framework} patterns
2. Include proper assertions
3. Use data-testid selectors
4. Generate page objects if a page/screen is mentioned
5. Return valid JSON matching this schema: {schema}

Only return JSON. No explanation. No markdown.
```

### 2.4 Code Generator (`generator/code_generator.py`)

**Responsibility:** Render Pydantic data into executable code.

**Dependencies:** `jinja2`

**Key functions:**
- `generate_test_code(test: GeneratedTest, template_path: Optional[Path]) -> Dict[str, str]`

Returns dict of `{filename: code_string}`.

**Built-in templates:**
- `playwright_spec.jinja2` — Playwright TypeScript test template
- `cypress_spec.jinja2` — Cypress TypeScript test template
- `playwright_page.jinja2` — Playwright page object template
- `cypress_page.jinja2` — Cypress page object template (commands)

**Template variables:**
```python
{
    "test_name": str,
    "describe_block": str,
    "scenarios": List[{
        "name": str,
        "steps": List[{"action": str, "selector": str, "value": str}],
        "assertions": List[str]
    }],
    "imports": List[str],
    "page_objects": Dict[str, List[{"name": str, "selector": str}]]
}
```

### 2.5 Output Writer (`writer/output_writer.py`)

**Responsibility:** Manage filesystem output safely.

**Dependencies:** `pathlib`

**Key functions:**
- `write_files(files: Dict[str, str], output_dir: Path, force: bool) -> List[Path]`
- `preview_files(files: Dict[str, str]) -> None` — dry-run display

**Safety guarantees:**
- Atomic writes: write to temp file, then rename
- Never overwrite without `--force`
- Create parent directories automatically

## 3. Data Flow (End to End)

```
Input: "User logs in with valid credentials, sees dashboard"

1. CLI Layer
   → Reads input as string
   → Validates --framework=playwright
   → Creates LLMConfig from env vars + CLI flags

2. Input Parser
   → Creates ScenarioInput(text="User logs in...", source="argument")
   → Returns [ScenarioInput(...)]

3. LLM Client
   → Builds prompt: "You are an expert QA engineer writing playwright tests..."
   → Sends to GPT-4o-mini
   → Receives JSON response
   → Parses into GeneratedTest Pydantic model

4. Code Generator
   → Loads playwright_spec.jinja2 template
   → Injects GeneratedTest data
   → Renders: login.spec.ts, pages/login.page.ts
   → Returns {"tests/login.spec.ts": "...code...", "pages/login.page.ts": "..."}

5. Output Writer
   → Checks if login.spec.ts exists (no overwrite without --force)
   → Creates tests/ and pages/ directories
   → Writes both files
   → Console: "✓ Created tests/login.spec.ts"
   → Console: "✓ Created pages/login.page.ts"
```

## 4. Component Diagram

```
┌──────────────────────────────────────────────────────────┐
│ testify (Python Package)                                 │
│                                                          │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │   CLI    │─▶│ Input Parser │─▶│   LLM Client     │   │
│  │ (typer)  │  │  (pathlib)   │  │ (openai/tenacity)│   │
│  └──────────┘  └──────────────┘  └────────┬─────────┘   │
│                                            │             │
│  ┌──────────────────┐  ┌──────────────────┘             │
│  │ Output Writer    │◀─│  Code Generator                │
│  │ (pathlib, rich)  │  │  (jinja2)                      │
│  └──────────────────┘  └──────────────────┘             │
│                                                          │
└──────────────────────────────────────────────────────────┘
         │                                               
         ▼                                               
┌──────────────────────────────────────────────────────────┐
│ External: LLM API (OpenAI / Anthropic)                   │
└──────────────────────────────────────────────────────────┘
```

## 5. Error Handling Strategy

```
Layer              Error Type                    Handling
─────────────────────────────────────────────────────────────
CLI                Invalid args                  Typer validates + prints help
CLI                File not found                Print error + exit code 1
Input Parser       Empty input                   Print "no scenarios found" + exit
LLM Client         API timeout                   Retry 3x with backoff, then error
LLM Client         Invalid JSON                  Retry with stricter prompt
LLM Client         Auth error (bad key)          Print clear message about API key
Code Generator     Invalid template              Fall back to built-in
Output Writer      Permission denied             Print path + permission error
Output Writer      File exists (no --force)      Print "use --force to overwrite"
```

## 6. Configuration Precedence

```
1. CLI flags (highest priority)
2. Environment variables (TESTIFY_*)
3. Local config file (.testify.toml)
4. User config file (~/.config/testify/config.toml)
5. Defaults (lowest priority)
```
