"""af index — build a structural index of a directory and register it for search with mks."""

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import typer

app = typer.Typer(invoke_without_command=True)

DATA_DIR = Path.home() / ".claude" / "data"
REGISTRY = DATA_DIR / "registry.json"

_IGNORE = {
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", "dist",
    "build", "target", ".next", ".egg-info",
}


def load_registry() -> dict:
    if REGISTRY.exists():
        return json.loads(REGISTRY.read_text())
    return {}


def save_registry(reg: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REGISTRY.write_text(json.dumps(reg, indent=2) + "\n")


def _file_count(path: Path) -> int:
    return sum(1 for f in path.rglob("*") if f.is_file() and f.name not in _IGNORE)


def build_tree(root: Path, prefix: str = "", depth: int = 0,
               max_depth: int = 0, show_files: bool = False) -> list[str]:
    """
    Compact tree renderer.
    - Directories always shown, with recursive file count.
    - Files shown only when show_files=True or when the directory has no subdirs (leaf).
    """
    lines = []
    try:
        entries = sorted(root.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    except PermissionError:
        return [f"{prefix}  <permission denied>"]

    dirs = [e for e in entries if e.is_dir() and not e.is_symlink() and e.name not in _IGNORE]
    files = [e for e in entries if e.is_file() and e.name not in _IGNORE]

    is_leaf = len(dirs) == 0
    show_files_here = show_files or is_leaf

    visible = dirs + (files if show_files_here else [])

    for i, entry in enumerate(visible):
        is_last = i == len(visible) - 1
        connector = "└── " if is_last else "├── "
        child_prefix = prefix + ("    " if is_last else "│   ")

        if entry.is_dir():
            count = _file_count(entry)
            lines.append(f"{prefix}{connector}{entry.name}/  ({count} files)")
            if max_depth == 0 or depth < max_depth - 1:
                lines.extend(build_tree(entry, child_prefix, depth + 1, max_depth, show_files))
        else:
            lines.append(f"{prefix}{connector}{entry.name}")

    return lines


@app.callback(invoke_without_command=True)
def main(
    path: Optional[str] = typer.Argument(None, help="Directory to index (default: cwd)"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Name for this data source"),
    depth: int = typer.Option(0, "--depth", "-d", help="Max tree depth (0 = unlimited)"),
    files: bool = typer.Option(False, "--files", "-f", help="Show all files (default: dirs + leaf files)"),
    no_mks: bool = typer.Option(False, "--no-mks", help="Skip mks collection registration"),
    list_: bool = typer.Option(False, "--list", "-l", help="List registered data sources"),
    remove: Optional[str] = typer.Option(None, "--remove", help="Remove a registered source by name"),
) -> None:
    """Build a structural index of a directory and register it for search with mks."""

    if list_:
        reg = load_registry()
        if not reg:
            typer.echo("No data sources registered. Run: af index <path>")
            return
        typer.echo("Registered data sources:\n")
        for n, meta in sorted(reg.items()):
            p = meta.get("path", "?")
            indexed = meta.get("last_indexed", "never")
            typer.echo(f"  {n:<22} {p}  ({indexed})")
        return

    if remove:
        reg = load_registry()
        if remove not in reg:
            typer.echo(f"Unknown source: '{remove}'", err=True)
            raise typer.Exit(1)
        del reg[remove]
        save_registry(reg)
        # Remove data dir
        source_dir = DATA_DIR / remove
        if source_dir.exists():
            import shutil
            shutil.rmtree(source_dir)
        typer.echo(f"Removed source '{remove}'. mks documents not removed — run: mks list --collection {remove} | mks remove <id> to clean up.")
        return

    root = Path(path).expanduser().resolve() if path else Path.cwd().resolve()
    if not root.is_dir():
        typer.echo(f"Not a directory: {root}", err=True)
        raise typer.Exit(1)

    source_name = name or root.name
    source_dir = DATA_DIR / source_name
    source_dir.mkdir(parents=True, exist_ok=True)

    typer.echo(f"Indexing '{root}' as '{source_name}'...")

    # Build structural tree
    typer.echo("  Building file tree...")
    tree_lines = [f"{root.name}/"]
    tree_lines.extend(build_tree(root, "", 0, depth, files))
    tree_body = "\n".join(tree_lines)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    tree_file = source_dir / "tree.md"
    tree_file.write_text(
        f"# {source_name} — file structure\n\n"
        f"**Path:** `{root}`  \n**Indexed:** {now}\n\n"
        f"```\n{tree_body}\n```\n"
    )
    typer.echo(f"  Tree → {tree_file}")

    # Register with mks. Collection name is the source name.
    if not no_mks:
        try:
            typer.echo(f"  Ingesting into mks collection '{source_name}' (may take a while)...")
            r = subprocess.run(
                ["mks", "add", str(root), "--collection", source_name],
                capture_output=True, text=True,
            )
            if r.returncode != 0:
                typer.echo(f"  mks add failed: {(r.stdout + r.stderr).strip()}", err=True)
            else:
                typer.echo(f"  mks collection '{source_name}' indexed")
        except FileNotFoundError:
            typer.echo("  [skip] mks not found — install: cargo install --path ~/projects/markstore", err=True)

    # Update registry
    reg = load_registry()
    reg[source_name] = {
        "path": str(root),
        "mks_collection": source_name,
        "last_indexed": now,
        "tree": str(tree_file),
    }
    save_registry(reg)

    typer.echo(f"\nDone.")
    typer.echo(f"  af search '<query>' --in {source_name}   # full-text search")
    typer.echo(f"  af search --tree --in {source_name}      # show file structure")
