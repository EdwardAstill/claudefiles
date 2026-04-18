"""af ak — agent knowledge index, scoped to research/knowledge/.

Reads only `research/knowledge/` (recursive). Other dirs under `research/`
(papers/, projects/, documentation/, lessons/) are raw inputs — not
queried via this CLI.

Commands:
  af ak list               index every .md file, show path + first heading
  af ak show <slug|path>   print one page
  af ak grep <pattern>     ripgrep over research/knowledge/
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import typer

app = typer.Typer(help="Index of the distilled agent knowledge (research/knowledge/).")

_KNOWLEDGE_ROOTS = [
    Path.cwd() / "research" / "knowledge",
    Path.home() / "projects" / "agentfiles" / "research" / "knowledge",
]


def _resolve_root() -> Path:
    for p in _KNOWLEDGE_ROOTS:
        if p.is_dir():
            return p
    typer.echo(
        "error: research/knowledge/ not found. Run from the agentfiles checkout.",
        err=True,
    )
    raise typer.Exit(code=2)


def _first_heading(path: Path) -> str:
    try:
        for line in path.read_text().splitlines()[:20]:
            if line.startswith("# "):
                return line[2:].strip()
    except OSError:
        pass
    return path.stem


def _resolve_page(root: Path, slug_or_path: str) -> Path | None:
    """Find a page by slug (e.g. 'harness-foundations') or relative path."""
    candidate = root / slug_or_path
    if candidate.is_file():
        return candidate
    candidate_md = root / f"{slug_or_path}.md"
    if candidate_md.is_file():
        return candidate_md
    matches = [p for p in root.rglob("*.md") if p.stem == slug_or_path]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        typer.echo(f"error: ambiguous slug '{slug_or_path}'. Matches:", err=True)
        for m in matches:
            typer.echo(f"  {m.relative_to(root)}", err=True)
        raise typer.Exit(code=2)
    return None


@app.command("list")
def list_cmd():
    """List every knowledge page with its first heading."""
    root = _resolve_root()
    pages = sorted(p for p in root.rglob("*.md") if p.name != "README.md")
    if not pages:
        typer.echo("(no knowledge pages yet — add files to research/knowledge/)")
        return
    for p in pages:
        rel = p.relative_to(root).with_suffix("")
        typer.echo(f"  {str(rel):<40}  {_first_heading(p)}")


@app.command("show")
def show_cmd(slug: str = typer.Argument(..., help="Page slug or relative path")):
    """Print a single knowledge page."""
    root = _resolve_root()
    page = _resolve_page(root, slug)
    if page is None:
        typer.echo(f"error: no knowledge page matches '{slug}'", err=True)
        raise typer.Exit(code=2)
    typer.echo(page.read_text())


@app.command("grep")
def grep_cmd(pattern: str = typer.Argument(..., help="Regex to search for")):
    """Search the knowledge dir with ripgrep."""
    root = _resolve_root()
    try:
        subprocess.run(["rg", "--smart-case", "--color=auto", pattern, str(root)], check=False)
    except FileNotFoundError:
        typer.echo("error: rg (ripgrep) not found on PATH", err=True)
        raise typer.Exit(code=127)
