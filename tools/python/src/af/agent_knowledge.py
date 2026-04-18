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


def _page_meta(path: Path) -> tuple[str, str]:
    """Return (id, heading) for a page. Empty id string if no frontmatter."""
    try:
        lines = path.read_text().splitlines()
    except OSError:
        return "", path.stem
    page_id = ""
    heading = path.stem
    in_frontmatter = False
    for i, line in enumerate(lines[:40]):
        stripped = line.strip()
        if i == 0 and stripped == "---":
            in_frontmatter = True
            continue
        if in_frontmatter:
            if stripped == "---":
                in_frontmatter = False
                continue
            if stripped.startswith("id:"):
                page_id = stripped.split(":", 1)[1].strip()
        elif line.startswith("# "):
            heading = line[2:].strip()
            break
    return page_id, heading


def _resolve_page(root: Path, slug_or_id: str) -> Path | None:
    """Find a page by id (e.g. 'K-003'), slug, or relative path."""
    # By id: scan frontmatter
    if slug_or_id.startswith("K-") or slug_or_id.startswith("k-"):
        target = slug_or_id.upper()
        for p in root.rglob("*.md"):
            if p.name == "README.md":
                continue
            page_id, _ = _page_meta(p)
            if page_id.upper() == target:
                return p
        return None
    # By path or slug
    candidate = root / slug_or_id
    if candidate.is_file():
        return candidate
    candidate_md = root / f"{slug_or_id}.md"
    if candidate_md.is_file():
        return candidate_md
    matches = [p for p in root.rglob("*.md") if p.stem == slug_or_id]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        typer.echo(f"error: ambiguous slug '{slug_or_id}'. Matches:", err=True)
        for m in matches:
            typer.echo(f"  {m.relative_to(root)}", err=True)
        raise typer.Exit(code=2)
    return None


@app.command("list")
def list_cmd():
    """List every knowledge page with its ID and first heading."""
    root = _resolve_root()
    pages = sorted(p for p in root.rglob("*.md") if p.name != "README.md")
    if not pages:
        typer.echo("(no knowledge pages yet — add files to research/knowledge/)")
        return
    for p in pages:
        rel = p.relative_to(root).with_suffix("")
        page_id, heading = _page_meta(p)
        id_col = page_id or "—"
        typer.echo(f"  {id_col:<7}  {str(rel):<34}  {heading}")


@app.command("show")
def show_cmd(slug: str = typer.Argument(..., help="Page slug, id (K-NNN), or relative path")):
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
