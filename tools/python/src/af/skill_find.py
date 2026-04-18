"""af skill-find — keyword search across SKILL.md frontmatter descriptions.

73 skills, no direct search. This reads every `agentfiles/**/SKILL.md`,
extracts the `description:` field, and ranks matches by keyword overlap.
"""

from __future__ import annotations

import re
from pathlib import Path

import typer

app = typer.Typer(help="Search skill descriptions.")


def _find_skills_root() -> Path | None:
    for p in (Path.cwd(), *Path.cwd().parents):
        if (p / "agentfiles").is_dir():
            return p / "agentfiles"
    fallback = Path.home() / "projects" / "agentfiles" / "agentfiles"
    return fallback if fallback.is_dir() else None


def _extract_description(md: Path) -> tuple[str, str]:
    """Return (name, description) from SKILL.md frontmatter."""
    name = md.parent.name
    desc = ""
    in_frontmatter = False
    capturing = False
    buf: list[str] = []
    for line in md.read_text().splitlines():
        stripped = line.rstrip()
        if stripped == "---":
            if not in_frontmatter:
                in_frontmatter = True
                continue
            break
        if not in_frontmatter:
            continue
        if stripped.startswith("name:"):
            name = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("description:"):
            rest = stripped.split(":", 1)[1].strip()
            if rest and rest != ">":
                desc = rest
            else:
                capturing = True
        elif capturing:
            if re.match(r"^\w+:", stripped):
                capturing = False
            else:
                buf.append(stripped.strip())
    if buf:
        desc = " ".join(buf).strip()
    return name, desc


@app.callback(invoke_without_command=True)
def find(
    query: str = typer.Argument(..., help="Keyword(s) to search for"),
    limit: int = typer.Option(10, "--limit", "-n"),
):
    """Search skill descriptions; print ranked matches."""
    root = _find_skills_root()
    if root is None:
        typer.echo("error: no agentfiles/ dir found (run from repo root)", err=True)
        raise typer.Exit(code=2)

    terms = [t.lower() for t in re.split(r"\s+", query.strip()) if t]
    if not terms:
        raise typer.Exit(code=0)

    results: list[tuple[int, str, str]] = []
    for md in root.rglob("SKILL.md"):
        if "agents" in md.parent.parts:
            continue
        name, desc = _extract_description(md)
        haystack = f"{name} {desc}".lower()
        score = sum(haystack.count(t) for t in terms)
        if score:
            results.append((score, name, desc))

    results.sort(key=lambda r: (-r[0], r[1]))
    if not results:
        typer.echo(f"(no matches for: {query})")
        return
    for score, name, desc in results[:limit]:
        first_sentence = desc.split(". ")[0][:100]
        typer.echo(f"  {score:>3}  {name:<35}  {first_sentence}")
