# testify — Product Requirements Document

## 1. Product Overview

**Product Name:** testify
**Tagline:** From spec to test.
**Description:** A CLI tool that accepts natural language acceptance criteria (user stories) and generates production-ready Playwright or Cypress test scripts with assertions, page objects, and data fixtures.

**Target Users:**
- QA Engineers writing automated tests daily
- SDETs building test infrastructure
- Developers who own quality but don't have dedicated QA

**Problem Statement:**
Writing automated tests is repetitive, time-consuming, and error-prone. QA engineers spend 40-60% of their time writing boilerplate test code instead of designing test strategies, exploring edge cases, or testing complex scenarios. Small teams without dedicated QA often skip automated tests entirely because the effort-to-value ratio feels too high.

**Solution:**
A CLI tool that bridges the gap between human-readable acceptance criteria and executable test code. QA engineers write what they want to test in plain language; testify generates the Playwright/Cypress code.

## 2. Goals & Non-Goals

### Goals
- Generate syntactically correct Playwright and Cypress test scripts from natural language input
- Support common testing patterns: assertions, page objects, data fixtures, hooks
- Provide CLI interface with stdin, file input, and directory batch modes
- Output organized test files that follow community best practices
- Keep generated code editable — no lock-in, no magic comments

### Non-Goals
- Not a test runner (delegates to Playwright/Cypress)
- Not a test orchestrator or CI tool
- Not a replacement for human test design — only generates from explicit specs
- Not a record-and-playback tool
- Will not handle complex test logic (loops, conditionals, state machines) in v1

## 3. User Stories

### US-01: Generate a single test from text
```
As a QA engineer
I want to pass a single acceptance criterion as text
So that I can quickly generate a test without creating a file
```

**Acceptance Criteria:**
- Command: `testify generate "User logs in with valid credentials"`
- Output: printed to stdout with syntax highlighting
- Supports `--framework playwright` and `--framework cypress`

### US-02: Generate tests from a spec file
```
As a QA engineer
I want to pass a file containing multiple acceptance criteria
So that I can batch-generate tests for a feature
```

**Acceptance Criteria:**
- Command: `testify generate spec.txt`
- File contains one acceptance criterion per line or markdown list
- Output: separate test files in `./tests/` directory
- Supports `--output` flag to specify target directory

### US-03: Generate tests from a directory
```
As a QA engineer  
I want to point testify at a directory of spec files
So that I can generate tests for an entire module at once
```

**Acceptance Criteria:**
- Command: `testify generate specs/`
- Recursively processes all `.md`, `.txt`, `.spec` files
- Maintains directory structure in output

### US-04: Specify test framework
```
As a QA engineer
I want to choose between Playwright and Cypress output
So that I can integrate testify with my existing test stack
```

**Acceptance Criteria:**
- `--framework playwright` (default) — generates `.spec.ts` with Playwright syntax
- `--framework cypress` — generates `.cy.ts` with Cypress syntax
- Generated code follows each framework's idiomatic patterns

### US-05: Generate with page objects
```
As a QA engineer
I want testify to extract page objects from my spec
So that I get maintainable, DRY test code
```

**Acceptance Criteria:**
- When spec mentions specific pages/screens, generate or reference page objects
- Page objects go into `pages/` directory
- Tests import page objects instead of inlining selectors

### US-06: Dry run mode
```
As a QA engineer
I want to preview what testify will generate without writing files
So that I can review before committing
```

**Acceptance Criteria:**
- `--dry-run` flag prints generated code to stdout
- Does not create any files
- Shows file names and paths that would be created

### US-07: Custom template support
```
As a power user
I want to provide custom templates for generated code
So that I can match my team's coding conventions
```

**Acceptance Criteria:**
- `--template` flag pointing to a template file
- Template uses variable injection for test name, steps, assertions
- Falls back to built-in templates if not provided

## 4. Constraints & Assumptions

**Constraints:**
- v1 targets Playwright (TypeScript) and Cypress (TypeScript) only
- CLI tool, not a library/API in v1
- LLM API calls require internet connection (v1)
- Generated code requires manual review before committing

**Assumptions:**
- Users have Node.js installed (for Playwright/Cypress)
- Users have Python 3.10+ installed (for the CLI)
- Acceptance criteria are written in English
- Each line/point describes one test scenario

## 5. Success Metrics

| Metric | Target |
|--------|--------|
| Time to generate a test from spec | < 5 seconds per scenario |
| Syntax validity of generated code | > 95% (no syntax errors in generated files) |
| Tests pass on first execution | > 70% (user may need minor adjustments) |
| User satisfaction (survey) | > 4/5 "would use again" |
| Generated code edit rate | < 30% of lines changed before commit |

## 6. Future Scope (v2+)

- Support for additional languages (Python Playwright, Java Selenium)
- VS Code extension for in-editor generation
- CI integration (GitHub Action, CircleCI orb)
- Test maintenance mode: re-generate tests when spec changes
- Learning mode: adapt generated code to user's past preferences
- Multi-step test generation from full user stories (Given-When-Then)
- Support for visual regression testing specs
