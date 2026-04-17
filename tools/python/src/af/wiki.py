"""af wiki — distilled index of the wiki/ directory.

One command: `af wiki list`. Prints the headings of every research page and
lesson, plus the paper count. Agents use this to check whether the wiki
already covers the ground before planning new work. For full-text search use
`rg wiki/`; for reading a page use `cat wiki/research/<slug>.md`.
"""

from __future__ import annotations

from pathlib import Path

import typer

app = typer.Typer(help="Index of the agentfiles wiki.")

_WIKI_ROOTS = [
    Path.cwd() / "wiki",
    Path.home() / "projects" / "agentfiles" / "wiki",
]


def _resolve_root() -> Path:
    for p in _WIKI_ROOTS:
        if p.is_dir():
            return p
    typer.echo("error: wiki/ not found. Run from the agentfiles checkout.", err=True)
    raise typer.Exit(code=2)


def _first_heading(path: Path) -> str:
    try:
        for line in path.read_text().splitlines()[:20]:
            if line.startswith("# "):
                return line[2:].strip()
    except OSError:
        pass
    return path.stem


@app.command("list")
def list_cmd():
    """Index research pages, lessons, and paper count."""
    root = _resolve_root()

    research = sorted((root / "research").glob("*.md"))
    lessons = sorted(
        (p for p in (root / "lessons-learned").glob("*.md") if p.name != "README.md"),
        reverse=True,
    )
    papers = list((root / "papers").glob("*.pdf")) if (root / "papers").is_dir() else []

    if research:
        typer.echo("research/")
        for p in research:
            typer.echo(f"  {p.stem:<30}  {_first_heading(p)}")

    if lessons:
        typer.echo("\nlessons-learned/")
        for p in lessons:
            typer.echo(f"  {p.stem:<40}  {_first_heading(p)}")

    typer.echo(f"\npapers/  {len(papers)} PDF(s) + link-only index at papers/README.md")
