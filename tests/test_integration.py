from pathlib import Path

from typer.testing import CliRunner

import testify.cli.commands as commands
from testify.cli.main import app
from testify.llm.schemas import GeneratedTest
from testify.llm.schemas import TestScenario as ScenarioModel
from testify.llm.schemas import TestStep as StepModel

runner = CliRunner()


class FakeLLMClient:
    instances = []

    def __init__(self, config=None):
        self.config = config
        self.calls = []
        FakeLLMClient.instances.append(self)

    def generate_test(self, scenario, framework):
        self.calls.append((scenario, framework))
        return GeneratedTest(
            filename="login.spec.ts",
            framework=framework,
            language="typescript",
            describe_block="Authentication",
            imports=[],
            scenarios=[
                ScenarioModel(
                    name=scenario.text,
                    description=scenario.text,
                    steps=[
                        StepModel(action="navigate", value="/login"),
                        StepModel(
                            action="fill email",
                            selector='[data-testid="email"]',
                            value="valid_user",
                        ),
                    ],
                    assertions=["Dashboard is visible"],
                )
            ],
        )


class OneFailureLLMClient(FakeLLMClient):
    def generate_test(self, scenario, framework):
        self.calls.append((scenario, framework))
        if "fails" in scenario.text:
            raise RuntimeError("LLM exploded")
        return super().generate_test(scenario, framework)


class AllFailureLLMClient(FakeLLMClient):
    def generate_test(self, scenario, framework):
        self.calls.append((scenario, framework))
        raise RuntimeError("LLM exploded")


def test_full_pipeline_with_mocked_llm_response(tmp_path, monkeypatch) -> None:
    FakeLLMClient.instances = []
    monkeypatch.setattr(commands, "LLMClient", FakeLLMClient)

    result = runner.invoke(
        app,
        [
            "generate",
            "User logs in",
            "--output",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    assert (tmp_path / "login.spec.ts").exists()
    assert 'test.describe("Authentication"' in (tmp_path / "login.spec.ts").read_text(
        encoding="utf-8"
    )
    assert FakeLLMClient.instances[0].calls[0][1] == "playwright"
    assert "Processed 1 scenario(s). Generated 1 file(s)." in result.output


def test_cli_flags_flow_through_to_modules(tmp_path, monkeypatch) -> None:
    captured = {}

    class CapturingLLMClient(FakeLLMClient):
        def generate_test(self, scenario, framework):
            captured["framework"] = framework
            return super().generate_test(scenario, framework)

    class CapturingCodeGenerator:
        def __init__(self, template_dir=None):
            captured["template_dir"] = template_dir

        def generate(self, test):
            captured["page_objects"] = test.page_objects
            captured["generated_framework"] = test.framework
            return {"login.cy.ts": "cy.visit('/');\n"}

    class CapturingOutputWriter:
        def __init__(self, console=None):
            captured["console"] = console

        def write(self, files, output_dir, force=False, dry_run=False):
            captured["files"] = files
            captured["output_dir"] = output_dir
            captured["force"] = force
            captured["dry_run"] = dry_run
            return [Path(output_dir) / "login.cy.ts"]

    monkeypatch.setattr(commands, "LLMClient", CapturingLLMClient)
    monkeypatch.setattr(commands, "CodeGenerator", CapturingCodeGenerator)
    monkeypatch.setattr(commands, "OutputWriter", CapturingOutputWriter)

    result = runner.invoke(
        app,
        [
            "generate",
            "User logs in",
            "--framework",
            "cypress",
            "--output",
            str(tmp_path / "out"),
            "--template",
            str(tmp_path / "templates"),
            "--force",
            "--no-page-objects",
            "--verbose",
        ],
    )

    assert result.exit_code == 0
    assert captured["framework"] == "cypress"
    assert captured["generated_framework"] == "cypress"
    assert captured["page_objects"] is None
    assert captured["template_dir"] == tmp_path / "templates"
    assert captured["output_dir"] == tmp_path / "out"
    assert captured["force"] is True
    assert captured["dry_run"] is False


def test_llm_failure_for_one_scenario_continues(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(commands, "LLMClient", OneFailureLLMClient)
    spec_file = tmp_path / "spec.txt"
    spec_file.write_text("User logs in\nThis scenario fails\n", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "generate",
            str(spec_file),
            "--output",
            str(tmp_path / "out"),
            "--verbose",
        ],
    )

    assert result.exit_code == 0
    assert (tmp_path / "out/login.spec.ts").exists()
    assert "Failed to generate test for: This scenario fails" in result.output
    assert "LLM exploded" in result.output
    assert "Processed 2 scenario(s). Generated 1 file(s)." in result.output


def test_all_llm_failures_exit_nonzero(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(commands, "LLMClient", AllFailureLLMClient)

    result = runner.invoke(
        app,
        [
            "generate",
            "User logs in",
            "--output",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 1
    assert "Failed to generate any tests" in result.output


def test_empty_input_exits_nonzero() -> None:
    result = runner.invoke(app, ["generate", "\n\n"])

    assert result.exit_code == 1
    assert "No scenarios found" in result.output


def test_dry_run_skips_llm_and_writes_no_files(tmp_path, monkeypatch) -> None:
    class FailingIfCalledLLMClient(FakeLLMClient):
        def generate_test(self, scenario, framework):
            raise AssertionError("LLM should not be called in dry-run")

    monkeypatch.setattr(commands, "LLMClient", FailingIfCalledLLMClient)

    result = runner.invoke(
        app,
        [
            "generate",
            "User logs in",
            "--dry-run",
            "--output",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    assert "? Would generate test for: User logs in" in result.output
    assert not any(tmp_path.iterdir())
