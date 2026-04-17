"""af session — session-level orchestration helpers.

The executor skill's Step 1 (Orient) runs a small sequence of discovery
commands at the start of every task: af context, af status, and af wiki list
if a wiki exists. This module packages that sequence into a single command so
agents and humans can run it with one invocation.

Commands:
    af session orient    run context + status + wiki list (skipping missing)
    af session summary   one-screen project fingerprint (concise orient)
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import typer

app = typer.Typer(help="Session-level orientation helpers.")


def _run(cmd: list[str]) -> int:
    result = subprocess.run(cmd)
    return result.returncode


def _heading(text: str):
    typer.echo(f"\n═══ {text} ═══")


@app.command("orient")
def orient_cmd(
    no_wiki: bool = typer.Option(
        False, "--no-wiki", help="Skip the wiki index step even if wiki/ exists."
    ),
):
    """Run af context, af status, and (if present) af wiki list in sequence.

    This is executor Step 1 as a single command. Use it at the start of any
    task — it's cheap and prevents re-orienting mid-work.
    """
    _heading("af context")
    _run(["af", "context"])

    _heading("af status")
    _run(["af", "status"])

    has_wiki = (Path.cwd() / "wiki").is_dir()
    if has_wiki and not no_wiki:
        _heading("af wiki list")
        _run(["af", "wiki", "list"])
    elif not has_wiki:
        typer.echo("\n(no wiki/ — skipping af wiki list)")


@app.command("summary")
def summary_cmd():
    """Compact one-screen fingerprint: context + uncommitted count + wiki count."""
    _heading("af context")
    _run(["af", "context"])

    # Lean signal from status — skip the full tree.
    typer.echo("\n═══ branch + uncommitted ═══")
    subprocess.run(
        ["git", "status", "--short", "--branch"], check=False
    )

    wiki = Path.cwd() / "wiki"
    if wiki.is_dir():
        research = list((wiki / "research").glob("*.md")) if (wiki / "research").is_dir() else []
        lessons = [
            p for p in (wiki / "lessons-learned").glob("*.md")
            if p.name != "README.md"
        ] if (wiki / "lessons-learned").is_dir() else []
        papers = list((wiki / "papers").glob("*.pdf")) if (wiki / "papers").is_dir() else []
        typer.echo(
            f"\nwiki:  {len(research)} research, {len(lessons)} lessons, "
            f"{len(papers)} papers  (af wiki list for details)"
        )
