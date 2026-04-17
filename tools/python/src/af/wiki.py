"""af wiki — make the wiki discoverable at the CLI level.

The wiki/ directory holds the system's long-term memory — research pages,
downloaded papers, and lessons learned. Agents are supposed to read the
relevant pages before making architectural decisions, but only if they can
find them. This CLI lowers the cost of "is there anything in the wiki about
X?" to one command.

Commands:
    af wiki list                     topic index across research + lessons
    af wiki grep "<pattern>"         ripgrep across wiki/ with context
    af wiki show <slug-or-path>      print one wiki file
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import typer

app = typer.Typer(help="Discover and grep the agentfiles wiki.")

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


@app.command("grep")
def grep_cmd(
    pattern: str = typer.Argument(..., help="Regex pattern to search for"),
    context: int = typer.Option(2, "-C", "--context", help="Lines of context around each match"),
):
    """Grep wiki/ with context. Falls back to plain Python if ripgrep is missing."""
    root = _resolve_root()
    rg = shutil.which("rg")
    if rg:
        result = subprocess.run(
            [rg, "--color=never", "-n", f"-C{context}", "-S", pattern, str(root)],
            capture_output=False,
        )
        raise typer.Exit(code=result.returncode)

    # Fallback: no rg available.
    try:
        regex = re.compile(pattern, re.IGNORECASE)
    except re.error as e:
        typer.echo(f"error: invalid regex: {e}", err=True)
        raise typer.Exit(code=2)
    any_hit = False
    for path in root.rglob("*.md"):
        lines = path.read_text().splitlines()
        for i, line in enumerate(lines):
            if regex.search(line):
                any_hit = True
                start = max(0, i - context)
                end = min(len(lines), i + context + 1)
                typer.echo(f"\n{path.relative_to(root)}:{i + 1}")
                for j in range(start, end):
                    marker = ">" if j == i else " "
                    typer.echo(f"  {marker} {j + 1}: {lines[j]}")
    raise typer.Exit(code=0 if any_hit else 1)


@app.command("show")
def show_cmd(target: str = typer.Argument(..., help="Slug (research/X, lessons/Y) or relative path")):
    """Print one wiki file to stdout. Accepts research/<slug>, lessons/<slug>, or a relative path."""
    root = _resolve_root()

    candidates = [
        root / target,
        root / f"{target}.md",
        root / "research" / f"{target}.md",
        root / "lessons-learned" / f"{target}.md",
    ]
    # Treat prefixes like "research/context-engineering" or "lessons/2026-04-18-foundational..."
    if target.startswith("lessons/"):
        candidates.append(root / "lessons-learned" / (target.split("/", 1)[1] + ".md"))

    for c in candidates:
        if c.is_file():
            typer.echo(c.read_text())
            return

    typer.echo(f"error: no wiki file matched '{target}'. try: af wiki list", err=True)
    raise typer.Exit(code=1)
