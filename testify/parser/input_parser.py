import sys
from pathlib import Path

from pydantic import BaseModel

SUPPORTED_SPEC_EXTENSIONS = {".txt", ".md", ".spec"}


class ScenarioInput(BaseModel):
    text: str
    source: str
    line_number: int | None = None


def parse_input(source: str | None = None) -> list[ScenarioInput]:
    """Parse scenarios from stdin, text, a file, or a directory."""
    if source is None:
        return parse_stdin()

    path = Path(source)
    if path.is_file():
        return parse_file(source)
    if path.is_dir():
        return parse_directory(source)

    return parse_text(source)


def parse_stdin() -> list[ScenarioInput]:
    """Read all stdin content and parse it into scenarios."""
    return _parse_lines(sys.stdin.read().splitlines(), source="stdin")


def parse_text(text: str, source: str = "argument") -> list[ScenarioInput]:
    """Parse raw text into scenarios, one non-empty line per scenario."""
    return _parse_lines(text.splitlines(), source=source)


def parse_file(path: str) -> list[ScenarioInput]:
    """Read a supported spec file and parse it into scenarios."""
    file_path = Path(path)
    return _parse_lines(file_path.read_text(encoding="utf-8").splitlines(), source=str(file_path))


def parse_directory(path: str) -> list[ScenarioInput]:
    """Recursively parse all supported spec files in a directory."""
    directory = Path(path)
    scenarios: list[ScenarioInput] = []

    for file_path in sorted(directory.rglob("*")):
        if file_path.is_file() and file_path.suffix in SUPPORTED_SPEC_EXTENSIONS:
            scenarios.extend(parse_file(str(file_path)))

    return scenarios


def _parse_lines(lines: list[str], source: str) -> list[ScenarioInput]:
    scenarios: list[ScenarioInput] = []

    for index, line in enumerate(lines, start=1):
        scenario_text = _normalize_line(line)
        if not scenario_text:
            continue

        scenarios.append(
            ScenarioInput(
                text=scenario_text,
                source=source,
                line_number=index,
            )
        )

    return scenarios


def _normalize_line(line: str) -> str:
    stripped = line.strip()
    if not stripped:
        return ""

    if stripped.startswith("- ") or stripped.startswith("* "):
        return stripped[2:].strip()

    return stripped
