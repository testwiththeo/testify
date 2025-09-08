from io import StringIO

from testify.parser import (
    ScenarioInput,
    parse_directory,
    parse_file,
    parse_input,
    parse_stdin,
    parse_text,
)


def test_plain_string_input() -> None:
    scenarios = parse_input("User logs in\nUser logs out")

    assert [scenario.text for scenario in scenarios] == ["User logs in", "User logs out"]
    assert [scenario.source for scenario in scenarios] == ["argument", "argument"]


def test_markdown_list_input() -> None:
    scenarios = parse_text("- User logs in\n* User logs out")

    assert [scenario.text for scenario in scenarios] == ["User logs in", "User logs out"]


def test_file_input(tmp_path) -> None:
    spec_file = tmp_path / "login.txt"
    spec_file.write_text("User logs in\n\nUser sees dashboard\n", encoding="utf-8")

    scenarios = parse_file(str(spec_file))

    assert [scenario.text for scenario in scenarios] == ["User logs in", "User sees dashboard"]
    assert [scenario.source for scenario in scenarios] == [str(spec_file), str(spec_file)]
    assert [scenario.line_number for scenario in scenarios] == [1, 3]


def test_directory_input_with_multiple_files(tmp_path) -> None:
    specs = tmp_path / "specs"
    nested = specs / "auth"
    nested.mkdir(parents=True)
    (specs / "dashboard.md").write_text("- User opens dashboard\n", encoding="utf-8")
    (nested / "login.spec").write_text("User logs in\n", encoding="utf-8")
    (nested / "ignored.json").write_text("Ignored scenario\n", encoding="utf-8")

    scenarios = parse_directory(str(specs))

    assert [scenario.text for scenario in scenarios] == ["User logs in", "User opens dashboard"]
    assert all(scenario.source.endswith((".md", ".spec")) for scenario in scenarios)


def test_stdin_input(monkeypatch) -> None:
    monkeypatch.setattr("sys.stdin", StringIO("User logs in\n* User logs out\n"))

    scenarios = parse_stdin()

    assert [scenario.text for scenario in scenarios] == ["User logs in", "User logs out"]
    assert [scenario.source for scenario in scenarios] == ["stdin", "stdin"]


def test_empty_input() -> None:
    assert parse_text("\n  \n") == []


def test_nonexistent_path_treated_as_string(tmp_path) -> None:
    missing_path = tmp_path / "missing.txt"

    scenarios = parse_input(str(missing_path))

    assert [scenario.text for scenario in scenarios] == [str(missing_path)]
    assert scenarios[0].source == "argument"


def test_line_numbers_are_correct() -> None:
    scenarios = parse_text("\n- User logs in\n\n* User logs out\nUser resets password")

    assert [scenario.line_number for scenario in scenarios] == [2, 4, 5]


def test_exports_scenario_input_model() -> None:
    scenario = ScenarioInput(text="User logs in", source="argument")

    assert scenario.text == "User logs in"
    assert scenario.source == "argument"
    assert scenario.line_number is None
