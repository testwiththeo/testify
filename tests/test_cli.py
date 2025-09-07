from pathlib import Path

from typer.testing import CliRunner

from testify.cli.main import app

runner = CliRunner()


def test_help_succeeds() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "generate" in result.output
    assert "init" in result.output
    assert "version" in result.output
    assert "list-models" in result.output


def test_generate_with_input() -> None:
    result = runner.invoke(app, ["generate", "User logs in"])
    assert result.exit_code == 0
    assert "input: User logs in" in result.output


def test_generate_with_all_options() -> None:
    result = runner.invoke(
        app,
        [
            "generate", "User logs in",
            "--framework", "cypress",
            "--output", "e2e",
            "--dry-run",
            "--force",
            "--no-page-objects",
            "--verbose",
            "--language", "typescript",
        ],
    )
    assert result.exit_code == 0
    assert "framework: cypress" in result.output
    assert "output: e2e" in result.output


def test_generate_invalid_framework() -> None:
    result = runner.invoke(app, ["generate", "User logs in", "--framework", "selenium"])
    assert result.exit_code != 0
    assert "playwright" in result.output
    assert "cypress" in result.output


def test_generate_dry_run() -> None:
    result = runner.invoke(app, ["generate", "User logs in", "--dry-run"])
    assert result.exit_code == 0
    assert "dry_run: True" in result.output


def test_init_creates_config(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    assert Path(".testify.toml").exists()


def test_version_command() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "testify v" in result.output


def test_version_option() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "testify v" in result.output


def test_list_models() -> None:
    result = runner.invoke(app, ["list-models"])
    assert result.exit_code == 0
    assert "gpt-4o-mini" in result.output
