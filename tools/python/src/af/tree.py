"""af tree — show folder structure as layered JSON."""

import json
import os
from pathlib import Path
from typing import Optional

import typer

app = typer.Typer(invoke_without_command=True)

# Default ignore patterns
_IGNORE = {
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", "dist",
    "build", ".egg-info", ".tox", ".next", "target",
}


def _build_tree(root: Path, depth: int, max_depth: int, ignore: set[str]) -> dict:
    """Recursively build a tree dict."""
    node: dict = {"name": root.name, "type": "directory", "children": []}

    if max_depth > 0 and depth >= max_depth:
        node["children"] = ["..."]
        return node

    try:
        entries = sorted(root.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    except PermissionError:
        node["children"] = ["<permission denied>"]
        return node

    for entry in entries:
        if entry.name in ignore or entry.name.endswith(".egg-info"):
            continue
        if entry.is_dir() and not entry.is_symlink():
            node["children"].append(_build_tree(entry, depth + 1, max_depth, ignore))
        else:
            child: dict = {"name": entry.name, "type": "file"}
            if entry.is_symlink():
                child["type"] = "symlink"
                try:
                    child["target"] = str(os.readlink(entry))
                except OSError:
                    child["target"] = "<broken>"
            node["children"].append(child)

    return node


def _print_text(node: dict, prefix: str = "", is_last: bool = True) -> list[str]:
    """Render tree as indented text lines."""
    lines = []
    connector = "└── " if is_last else "├── "
    name = node["name"]
    if node.get("type") == "symlink":
        name += f" → {node.get('target', '?')}"
    elif node.get("type") == "directory":
        name += "/"

    lines.append(f"{prefix}{connector}{name}")

    children = node.get("children", [])
    extension = "    " if is_last else "│   "
    for i, child in enumerate(children):
        if isinstance(child, str):
            lines.append(f"{prefix}{extension}└── {child}")
        else:
            lines.extend(_print_text(child, prefix + extension, i == len(children) - 1))

    return lines


@app.callback(invoke_without_command=True)
def main(
    path: Optional[str] = typer.Argument(None, help="Directory to scan (default: cwd)"),
    depth: int = typer.Option(0, "--depth", "-d", help="Max depth (0 = unlimited)"),
    output_json: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
    no_ignore: bool = typer.Option(False, "--no-ignore", help="Don't skip .git, node_modules, etc."),
    write: bool = typer.Option(False, "--write", help="Save to .agentfiles/tree.json"),
):
    """Show folder structure as a layered tree."""
    root = Path(path) if path else Path.cwd()
    if not root.is_dir():
        typer.echo(f"Not a directory: {root}", err=True)
        raise typer.Exit(1)

    ignore = set() if no_ignore else _IGNORE
    tree = _build_tree(root, 0, depth, ignore)

    if output_json or write:
        out = json.dumps(tree, indent=2)
        if write:
            bus = Path(".agentfiles")
            bus.mkdir(exist_ok=True)
            (bus / "tree.json").write_text(out + "\n")
            typer.echo(f"Written to .agentfiles/tree.json", err=True)
        if output_json:
            typer.echo(out)
        elif not write:
            typer.echo(out)
    else:
        # Text tree output
        typer.echo(f"{root.name}/")
        children = tree.get("children", [])
        for i, child in enumerate(children):
            if isinstance(child, str):
                typer.echo(f"└── {child}")
            else:
                for line in _print_text(child, "", i == len(children) - 1):
                    typer.echo(line)
