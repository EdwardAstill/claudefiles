"""cf search — search indexed data sources via qmd."""

import json
import subprocess
from pathlib import Path
from typing import Optional

import typer

app = typer.Typer(invoke_without_command=True)

DATA_DIR = Path.home() / ".claude" / "data"
REGISTRY = DATA_DIR / "registry.json"


def load_registry() -> dict:
    if REGISTRY.exists():
        return json.loads(REGISTRY.read_text())
    return {}


@app.callback(invoke_without_command=True)
def main(
    query: Optional[list[str]] = typer.Argument(None, help="Search query (words or quoted phrase)"),
    source: Optional[str] = typer.Option(None, "--source", "-s", help="Data source name to search"),
    mode: str = typer.Option("query", "--mode", "-m", help="qmd mode: query, search, vsearch"),
    limit: int = typer.Option(10, "--limit", "-n", help="Max results"),
    full: bool = typer.Option(False, "--full", help="Show full document instead of snippet"),
    files_only: bool = typer.Option(False, "--files", help="Return file paths only"),
    tree: bool = typer.Option(False, "--tree", "-t", help="Show structural file tree for a source"),
    list_: bool = typer.Option(False, "--list", "-l", help="List all registered data sources"),
) -> None:
    """Search indexed data sources. Use --in to target a specific source."""

    reg = load_registry()

    query_str = " ".join(query) if query else None

    if list_ or (query_str is None and not tree):
        if not reg:
            typer.echo("No data sources indexed yet. Run: cf index <path> [--name <name>]")
            return
        typer.echo("Indexed data sources:\n")
        for n, meta in sorted(reg.items()):
            typer.echo(f"  {n:<22} {meta.get('path', '?')}")
        typer.echo(f"\nUsage:")
        typer.echo(f"  cf search '<query>'                  # search all sources")
        typer.echo(f"  cf search '<query>' --source notes   # search a specific source")
        typer.echo(f"  cf search --tree --source notes      # show file structure")
        return

    if tree:
        if not source:
            if reg:
                typer.echo("Specify a source with --source <name>. Available:", err=True)
                for n in sorted(reg):
                    typer.echo(f"  {n}", err=True)
            else:
                typer.echo("No sources indexed. Run: cf index <path>", err=True)
            raise typer.Exit(1)
        if source not in reg:
            typer.echo(f"Unknown source '{source}'. Run: cf search --list", err=True)
            raise typer.Exit(1)
        tree_file = Path(reg[source]["tree"])
        if tree_file.exists():
            typer.echo(tree_file.read_text())
        else:
            typer.echo(f"Tree not found — re-run: cf index {reg[source]['path']} --name {source}", err=True)
            raise typer.Exit(1)
        return

    if not query_str:
        typer.echo("Provide a query. Usage: cf search --source <name> <query>", err=True)
        raise typer.Exit(1)

    # Validate source name and resolve qmd collection name
    qmd_collection = None
    if source:
        if source not in reg:
            typer.echo(f"Unknown source '{source}'. Run: cf search --list", err=True)
            raise typer.Exit(1)
        qmd_collection = reg[source].get("qmd_collection", source)

    # Build qmd command
    cmd = ["qmd", mode, query_str, "-n", str(limit)]
    if qmd_collection:
        cmd += ["-c", qmd_collection]
    if full:
        cmd += ["--full"]
    if files_only:
        cmd += ["--files"]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.stdout:
            typer.echo(result.stdout)
        if result.stderr:
            typer.echo(result.stderr, err=True)
        if result.returncode != 0:
            raise typer.Exit(result.returncode)
    except FileNotFoundError:
        typer.echo("qmd not found. Install: bun install -g @tobilu/qmd", err=True)
        raise typer.Exit(1)
