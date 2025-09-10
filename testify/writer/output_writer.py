from pathlib import Path

from rich.console import Console


class OutputWriter:
    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console()

    def write(
        self,
        files: dict[str, str],
        output_dir: Path,
        force: bool = False,
        dry_run: bool = False,
    ) -> list[Path]:
        """Write generated files to disk and return the paths written."""
        base_dir = Path(output_dir)

        if dry_run:
            self._preview(files)
            return []

        written_paths: list[Path] = []
        for relative_path, content in files.items():
            target_path = base_dir / relative_path

            if target_path.exists() and not force:
                self.console.print(
                    f"[yellow]⚠ Skipped {relative_path} (use --force to overwrite)[/yellow]"
                )
                continue

            try:
                written_path = self._write_file(target_path, content, force=force)
            except PermissionError:
                self.console.print(f"[red]Permission denied writing {target_path}[/red]")
                raise

            written_paths.append(written_path)
            self.console.print(f"[green]✓ Created {relative_path}[/green]")

        self.console.print(f"[green]Done! Generated {len(written_paths)} file(s).[/green]")
        return written_paths

    def _write_file(self, path: Path, content: str, force: bool) -> Path:
        if path.exists() and not force:
            raise FileExistsError(f"{path} already exists. Use --force to overwrite.")

        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self._tmp_path(path)

        try:
            tmp_path.write_text(content, encoding="utf-8")
            self._replace_tmp(tmp_path, path)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

        return path

    def _preview(self, files: dict[str, str]) -> None:
        for relative_path in files:
            self.console.print(f"[blue]? Would create {relative_path}[/blue]")

    def _tmp_path(self, path: Path) -> Path:
        return path.with_name(f".{path.name}.tmp")

    def _replace_tmp(self, tmp_path: Path, path: Path) -> None:
        tmp_path.replace(path)
