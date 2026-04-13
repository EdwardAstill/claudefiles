"""af search — search indexed data sources via mks (markstore)."""

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


def _build_mks_query(mode: str, query_str: str) -> str:
    """Translate search mode to mks query prefix."""
    if mode == "vsearch":
        return f"vec: {query_str}"
    elif mode == "search":
        return f"lex: {query_str}"
    else:  # query (default) — BM25
        return query_str


@app.callback(invoke_without_command=True)
def main(
    query: Optional[list[str]] = typer.Argument(None, help="Search query (words or quoted phrase)"),
    source: Optional[str] = typer.Option(None, "--source", "-s", help="Data source name to search"),
    mode: str = typer.Option("query", "--mode", "-m", help="Search mode: query/search (BM25), vsearch (vector)"),
    limit: int = typer.Option(10, "--limit", "-n", help="Max results"),
    snippets: bool = typer.Option(False, "--snippets", help="Show text snippets in results"),
    tree: bool = typer.Option(False, "--tree", "-t", help="Show structural file tree for a source"),
    list_: bool = typer.Option(False, "--list", "-l", help="List all registered data sources"),
) -> None:
    """Search indexed data sources."""

    reg = load_registry()

    query_str = " ".join(query) if query else None

    if list_ or (query_str is None and not tree):
        if not reg:
            typer.echo("No data sources indexed yet. Run: af index <path> [--name <name>]")
            return
        typer.echo("Indexed data sources:\n")
        for n, meta in sorted(reg.items()):
            typer.echo(f"  {n:<22} {meta.get('path', '?')}")
        typer.echo(f"\nUsage:")
        typer.echo(f"  af search '<query>'                  # search all sources")
        typer.echo(f"  af search '<query>' --source notes   # search a specific source")
        typer.echo(f"  af search --tree --source notes      # show file structure")
        return

    if tree:
        if not source:
            if reg:
                typer.echo("Specify a source with --source <name>. Available:", err=True)
                for n in sorted(reg):
                    typer.echo(f"  {n}", err=True)
            else:
                typer.echo("No sources indexed. Run: af index <path>", err=True)
            raise typer.Exit(1)
        if source not in reg:
            typer.echo(f"Unknown source '{source}'. Run: af search --list", err=True)
            raise typer.Exit(1)
        tree_file = Path(reg[source]["tree"])
        if tree_file.exists():
            typer.echo(tree_file.read_text())
        else:
            typer.echo(f"Tree not found — re-run: af index {reg[source]['path']} --name {source}", err=True)
            raise typer.Exit(1)
        return

    if not query_str:
        typer.echo("Provide a query. Usage: af search --source <name> <query>", err=True)
        raise typer.Exit(1)

    # Resolve mks collection name (support legacy qmd_collection key)
    mks_collection = None
    if source:
        if source not in reg:
            typer.echo(f"Unknown source '{source}'. Run: af search --list", err=True)
            raise typer.Exit(1)
        mks_collection = (
            reg[source].get("mks_collection")
            or reg[source].get("qmd_collection")
            or source
        )

    # Build mks command
    mks_query = _build_mks_query(mode, query_str)
    cmd = ["mks", "search", mks_query, "--limit", str(limit)]
    if mks_collection:
        cmd += ["--collection", mks_collection]
    if snippets:
        cmd += ["--snippets"]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.stdout:
            typer.echo(result.stdout)
        if result.stderr:
            typer.echo(result.stderr, err=True)
        if result.returncode != 0:
            raise typer.Exit(result.returncode)
    except FileNotFoundError:
        typer.echo("mks not found. Install: cargo install --path ~/projects/markstore", err=True)
        raise typer.Exit(1)
