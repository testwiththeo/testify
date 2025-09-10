from io import StringIO
from pathlib import Path

from rich.console import Console

from testify.writer import OutputWriter


def test_write_files_creates_expected_content(tmp_path) -> None:
    writer = OutputWriter(console=_console())

    written = writer.write({"tests/login.spec.ts": "test code"}, tmp_path)

    target = tmp_path / "tests/login.spec.ts"
    assert written == [target]
    assert target.read_text(encoding="utf-8") == "test code"


def test_existing_file_without_force_is_not_overwritten(tmp_path) -> None:
    target = tmp_path / "tests/login.spec.ts"
    target.parent.mkdir(parents=True)
    target.write_text("existing", encoding="utf-8")
    output = StringIO()
    writer = OutputWriter(console=_console(output))

    written = writer.write({"tests/login.spec.ts": "new"}, tmp_path)

    assert written == []
    assert target.read_text(encoding="utf-8") == "existing"
    assert "⚠ Skipped tests/login.spec.ts (use --force to overwrite)" in output.getvalue()
    assert "use --force to overwrite" in output.getvalue()


def test_existing_file_with_force_is_overwritten(tmp_path) -> None:
    target = tmp_path / "tests/login.spec.ts"
    target.parent.mkdir(parents=True)
    target.write_text("existing", encoding="utf-8")
    writer = OutputWriter(console=_console())

    written = writer.write({"tests/login.spec.ts": "new"}, tmp_path, force=True)

    assert written == [target]
    assert target.read_text(encoding="utf-8") == "new"


def test_dry_run_does_not_create_files(tmp_path) -> None:
    output = StringIO()
    writer = OutputWriter(console=_console(output))

    written = writer.write({"tests/login.spec.ts": "test code"}, tmp_path, dry_run=True)

    assert written == []
    assert not (tmp_path / "tests/login.spec.ts").exists()
    assert not (tmp_path / "tests").exists()
    assert "? Would create tests/login.spec.ts" in output.getvalue()


def test_atomic_write_uses_tmp_file_then_replace(tmp_path) -> None:
    writer = OutputWriter(console=_console())
    observed = {}

    def replace_tmp(tmp_path_arg: Path, path_arg: Path) -> None:
        observed["tmp_path"] = tmp_path_arg
        observed["target_path"] = path_arg
        observed["tmp_exists_before_replace"] = tmp_path_arg.exists()
        tmp_path_arg.replace(path_arg)

    writer._replace_tmp = replace_tmp

    writer.write({"tests/login.spec.ts": "test code"}, tmp_path)

    assert observed["tmp_path"] == tmp_path / "tests/.login.spec.ts.tmp"
    assert observed["target_path"] == tmp_path / "tests/login.spec.ts"
    assert observed["tmp_exists_before_replace"] is True
    assert not observed["tmp_path"].exists()


def test_directory_structure_is_auto_created(tmp_path) -> None:
    writer = OutputWriter(console=_console())

    writer.write({"tests/auth/login.spec.ts": "test code", "pages/login.page.ts": "page"}, tmp_path)

    assert (tmp_path / "tests/auth/login.spec.ts").exists()
    assert (tmp_path / "pages/login.page.ts").exists()


def test_summary_prints_written_count(tmp_path) -> None:
    output = StringIO()
    writer = OutputWriter(console=_console(output))

    writer.write(
        {
            "tests/login.spec.ts": "test code",
            "pages/login.page.ts": "page",
        },
        tmp_path,
    )

    assert "✓ Created tests/login.spec.ts" in output.getvalue()
    assert "Done! Generated 2 file(s)." in output.getvalue()


def _console(file=None) -> Console:
    return Console(file=file or StringIO(), force_terminal=False, color_system=None)
