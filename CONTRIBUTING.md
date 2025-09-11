# Contributing to testify

Thanks for improving testify. This project is a Python CLI, and changes should stay small, tested, and easy to review.

## Development Setup

```bash
git clone https://github.com/yourusername/testify.git
cd testify
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

Set an API key only when running real generation:

```bash
export TESTIFY_LLM_API_KEY="sk-..."
```

The test suite mocks LLM behavior and should not require a real API key.

## Running Tests

```bash
pytest
pytest --cov=testify
```

Run targeted tests while developing:

```bash
pytest tests/test_input_parser.py
pytest tests/test_llm_client.py
pytest tests/test_code_generator.py
pytest tests/test_output_writer.py
pytest tests/test_integration.py
```

## Code Style

Use Ruff and mypy before opening a pull request:

```bash
ruff check testify/
mypy testify/
```

Guidelines:

- Prefer typed public functions.
- Keep modules focused on their documented responsibility.
- Do not make live LLM calls in tests.
- Keep generated test code editable and free of secrets.
- Never overwrite user files unless the caller passed `--force`.

## Pull Request Process

1. Open an issue or describe the problem clearly in the pull request.
2. Add or update tests for behavior changes.
3. Run `pytest --cov=testify`, `ruff check testify/`, and `mypy testify/`.
4. Keep the pull request focused on one logical change.
5. Document user-facing changes in `README.md` when needed.

## Release Checklist

```bash
python -m build
twine check dist/*
```

Only publish after tests, linting, type checking, and package checks pass.
