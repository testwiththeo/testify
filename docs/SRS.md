# testify — Software Requirements Specification

## 1. System Overview

testify is a CLI tool that translates natural language acceptance criteria into executable test scripts. It uses an LLM to parse natural language and generate structured test code, then writes well-organized test files to disk.

## 2. Functional Requirements

### FR-01: CLI Entry Point

**ID:** FR-01
**Description:** The tool exposes a `testify` command with subcommands.
**Priority:** P0

```
testify generate [INPUT] [OPTIONS]
```

**Options:**
| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--framework` | string | `playwright` | Target test framework (`playwright` or `cypress`) |
| `--output` | string | `./tests` | Output directory for generated tests |
| `--dry-run` | bool | `false` | Print output to stdout without writing files |
| `--template` | string | built-in | Path to custom Jinja2 template |
| `--language` | string | `typescript` | Output language (`typescript` only in v1) |
| `--verbose` | bool | `false` | Enable detailed logging |

### FR-02: Input Parsing

**ID:** FR-02
**Description:** Parse input from multiple sources.
**Priority:** P0

- **stdin:** `echo "User logs in" \| testify generate`
- **string argument:** `testify generate "User logs in with valid password"`
- **file:** `testify generate spec.txt` — reads all lines
- **directory:** `testify generate specs/` — reads all `.txt`, `.md`, `.spec` files

When reading files, support two formats:
1. One acceptance criterion per line
2. Markdown unordered list items (`- User logs in`)

### FR-03: LLM Integration

**ID:** FR-03
**Description:** Send parsed input to an LLM for structured test generation.
**Priority:** P0

**Requirements:**
- Default provider: OpenAI GPT-4o-mini (cost-optimized)
- Configurable provider: `--provider` flag or `TESTIFY_LLM_PROVIDER` env var
- Configurable model: `--model` flag or `TESTIFY_LLM_MODEL` env var
- API key via environment variable: `TESTIFY_LLM_API_KEY` or `OPENAI_API_KEY`
- Output must be structured JSON following a defined schema (Pydantic model)
- LLM timeout: 30 seconds
- Retry: 3 attempts with exponential backoff
- Fallback: if LLM call fails, output a clear error message with the raw input

**Prompt Design:**
- System prompt: defines the role (expert QA engineer writing tests)
- User prompt: contains the acceptance criteria + framework + instructions
- Output format: structured JSON matching the TestSchema Pydantic model

### FR-04: Test Code Generation

**ID:** FR-04
**Description:** Convert structured LLM output into syntactically valid test files.
**Priority:** P0

**Generated file structure for `playwright`:**
```typescript
// tests/login.spec.ts
import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/login.page';

test.describe('Authentication', () => {
  test('User logs in with valid credentials, sees dashboard', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.fillCredentials('valid_user', 'valid_password');
    await loginPage.submit();
    await expect(page).toHaveURL(/.*dashboard/);
    await expect(page.locator('h1')).toHaveText('Dashboard');
  });
});
```

**Generated file structure for `cypress`:**
```typescript
// tests/login.cy.ts
describe('Authentication', () => {
  it('User logs in with valid credentials, sees dashboard', () => {
    cy.visit('/login');
    cy.get('[data-cy=email]').type('valid_user');
    cy.get('[data-cy=password]').type('valid_password');
    cy.get('[data-cy=submit]').click();
    cy.url().should('include', '/dashboard');
    cy.get('h1').should('contain', 'Dashboard');
  });
});
```

### FR-05: Page Object Generation

**ID:** FR-05
**Description:** Optionally generate page object files alongside tests.
**Priority:** P1

- When input references specific pages/screens, extract page objects
- Default data-testid selectors: `[data-testid=element-name]`
- Page objects go in `pages/` directory
- Each page object file exports a class
- Tests import page objects via relative import

### FR-06: Output Management

**ID:** FR-06
**Description:** Write generated files to disk in organized structure.
**Priority:** P0

```
tests/
  auth/
    login.spec.ts
    logout.spec.ts
  dashboard/
    overview.spec.ts
pages/
  login.page.ts
  dashboard.page.ts
```

- Naming convention: based on first noun + action in the spec
- Overwrite behavior: never overwrite existing files without `--force` flag
- Logging: print created file paths on success

### FR-07: Error Handling

**ID:** FR-07
**Description:** Graceful error handling for all failure modes.
**Priority:** P1

| Scenario | Behavior |
|----------|----------|
| Empty input | Print usage + error message |
| Invalid framework name | Print supported frameworks + exit |
| LLM API timeout | Retry 3 times, then print clear error |
| LLM returns invalid JSON | Retry with stricter prompt, then error |
| Output directory not writable | Print permission error |
| Network error | Print connectivity error |
| Invalid template | Fall back to built-in template |

### FR-08: Configuration

**ID:** FR-08
**Description:** Support configuration via environment variables and config file.
**Priority:** P2

Environment variables:
- `TESTIFY_LLM_PROVIDER` — LLM provider (default: `openai`)
- `TESTIFY_LLM_MODEL` — Model name (default: `gpt-4o-mini`)
- `TESTIFY_LLM_API_KEY` — API key
- `TESTIFY_DEFAULT_FRAMEWORK` — Default output framework
- `TESTIFY_OUTPUT_DIR` — Default output directory

Config file: `~/.config/testify/config.toml` or `./.testify.toml`

## 3. Non-Functional Requirements

### NFR-01: Performance
- Cold start: < 2 seconds (Python startup + imports)
- Generation: < 5 seconds per scenario (including LLM call)
- Batch of 10 scenarios: < 30 seconds
- Memory: < 200MB RAM

### NFR-02: Reliability
- 99% uptime of the CLI (it doesn't depend on a server, only LLM API)
- LLM API failure rate: handle gracefully > 99% of cases
- No data loss: never overwrite user files without explicit flag

### NFR-03: Usability
- Help text accessible via `testify --help`
- Clear error messages with suggested fixes
- Sensible defaults (generate Playwright TS tests in `./tests/`)
- Colored output for readability (rich library)

### NFR-04: Security
- API key never stored in project files
- API key only read from environment variables or config file
- Generated code contains no secrets or credentials
- No telemetry or data collection in v1

## 4. Interface Specification

### 4.1 CLI Interface

```
Usage: testify [OPTIONS] COMMAND [ARGS]...

  testify generate [INPUT] [OPTIONS]
  testify init                          # Create .testify.toml config
  testify version                       # Print version
  testify list-models                   # List available LLM models

Options:
  --help          Show this message and exit.
  --version       Show version and exit.
  --verbose, -v   Enable verbose output.

Generate Options:
  INPUT                     Input text, file, or directory (default: stdin)
  --framework, -f TEXT      Target framework [playwright|cypress]
  --output, -o TEXT         Output directory
  --dry-run, -d             Preview output without writing
  --template, -t TEXT       Custom template file
  --force                   Overwrite existing files
  --no-page-objects         Skip page object generation
```

### 4.2 LLM Output Schema (Pydantic)

```python
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

class GeneratedTest(BaseModel):
    filename: str
    framework: str
    language: str
    imports: List[str]
    describe_block: str
    scenarios: List[TestScenario]
    page_objects: Optional[Dict[str, List[Dict]]] = None
```
