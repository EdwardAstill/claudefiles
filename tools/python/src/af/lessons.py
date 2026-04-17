"""af lessons — scaffold and list wiki/lessons-learned/ entries.

The wiki's lessons-learned folder is where session findings crystallise into
durable notes. A lesson should capture: what was tried, what worked or didn't,
and the specific situation where that lesson applies. This CLI removes the
friction of creating one.

Commands:
    af lessons new "<title>"     scaffold a new dated file + open in $EDITOR
    af lessons list              list existing lessons newest-first
"""

from __future__ import annotations

import os
import re
import subprocess
from datetime import date
from pathlib import Path

import typer

app = typer.Typer(help="Capture and list wiki lessons-learned entries.")

_WIKI_PATHS = [
    Path.cwd() / "wiki" / "lessons-learned",
    Path.home() / "projects" / "agentfiles" / "wiki" / "lessons-learned",
]


def _resolve_dir() -> Path:
    for p in _WIKI_PATHS:
        if p.is_dir():
            return p
    fallback = _WIKI_PATHS[-1]
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def _slug(title: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return s[:60] or "lesson"


_TEMPLATE = """# {title}

## Context

What was happening. One or two sentences.

## What happened

What was tried; what surprised you.

## The lesson

One sentence that a future agent or the user could pattern-match on.

## Where this applies

Situations where this lesson should change the default behaviour.

## References

- Session branch / commits:
- Related wiki pages:
- Primary sources:
"""


@app.command("new")
def new_cmd(title: str = typer.Argument(..., help="Short human title for the lesson")):
    """Create a dated lessons-learned markdown file and print its path."""
    lessons_dir = _resolve_dir()
    today = date.today().isoformat()
    slug = _slug(title)
    path = lessons_dir / f"{today}-{slug}.md"

    if path.exists():
        typer.echo(f"already exists: {path}")
        raise typer.Exit(code=1)

    path.write_text(_TEMPLATE.format(title=title))
    typer.echo(str(path))

    editor = os.environ.get("EDITOR")
    if editor and sys_stdout_is_tty():
        try:
            subprocess.run([editor, str(path)], check=False)
        except FileNotFoundError:
            pass


@app.command("list")
def list_cmd():
    """List existing lessons newest-first."""
    lessons_dir = _resolve_dir()
    entries = sorted(
        (p for p in lessons_dir.glob("*.md") if p.name != "README.md"),
        reverse=True,
    )
    if not entries:
        typer.echo("no lessons captured yet. start with: af lessons new \"<title>\"")
        return
    for p in entries:
        typer.echo(p.name)


def sys_stdout_is_tty() -> bool:
    import sys as _sys
    return _sys.stdout.isatty()
