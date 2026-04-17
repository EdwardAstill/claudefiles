"""af archetype — match user intent against the task-archetypes registry.

The registry (docs/reference/task-archetypes.json) enumerates big-task shapes
mapped to agent group compositions. This module turns it from passive reference
into an active routing helper: given a short user phrasing, return the best
matching archetype plus its phase layout, so executor/manager can lift the
plan instead of designing one from scratch.

Commands:
    af archetype list
    af archetype show <id>
    af archetype match "<user text>" [--top 3]
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import typer

app = typer.Typer(help="Task-archetypes registry helpers.")

_REGISTRY_PATHS = [
    # Project-relative when run from the agentfiles checkout.
    Path.cwd() / "docs" / "reference" / "task-archetypes.json",
    # Installed global copy, if symlinked.
    Path.home() / ".claude" / "agentfiles" / "docs" / "reference" / "task-archetypes.json",
    # Source-of-truth checkout.
    Path.home() / "projects" / "agentfiles" / "docs" / "reference" / "task-archetypes.json",
]


def _load() -> dict:
    for p in _REGISTRY_PATHS:
        if p.is_file():
            return json.loads(p.read_text())
    typer.echo(
        "error: task-archetypes.json not found. Looked in:\n  "
        + "\n  ".join(str(p) for p in _REGISTRY_PATHS),
        err=True,
    )
    raise typer.Exit(code=2)


_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "to", "of", "in", "on", "at", "for",
    "with", "by", "from", "as", "is", "are", "was", "be", "this", "that", "it",
    "i", "we", "me", "my", "you", "your", "need", "want", "please", "can",
}


def _tokens(text: str) -> set[str]:
    return {t for t in _TOKEN_RE.findall(text.lower()) if t not in _STOPWORDS and len(t) > 1}


def _score(user_tokens: set[str], archetype: dict) -> int:
    score = 0
    for phrase in archetype.get("signal_phrases", []):
        overlap = user_tokens & _tokens(phrase)
        score += len(overlap) * (2 if len(overlap) >= 2 else 1)
    score += len(user_tokens & _tokens(archetype.get("name", "")))
    return score


def _fmt_phases(archetype: dict) -> str:
    lines = []
    for i, phase in enumerate(archetype.get("phases", []), 1):
        par = "parallel" if phase.get("parallel") else "sequential"
        agents = ", ".join(phase.get("agents", []))
        lines.append(f"  {i}. [{phase['phase']}] {par} — {agents}")
        lines.append(f"       produces: {phase.get('produces', '?')}")
    return "\n".join(lines)


@app.command("list")
def list_cmd():
    """List every archetype id and one-line name."""
    data = _load()
    for a in data["archetypes"]:
        typer.echo(f"{a['id']:<36} {a['name']}")


@app.command("show")
def show_cmd(archetype_id: str):
    """Print the full phase layout for one archetype."""
    data = _load()
    for a in data["archetypes"]:
        if a["id"] == archetype_id:
            typer.echo(f"{a['id']} — {a['name']}")
            typer.echo(f"scale: {a.get('typical_scale', '?')}")
            typer.echo("phases:")
            typer.echo(_fmt_phases(a))
            if a.get("risks"):
                typer.echo(f"risks: {', '.join(a['risks'])}")
            if a.get("notes"):
                typer.echo(f"notes: {a['notes']}")
            return
    typer.echo(f"error: no archetype with id '{archetype_id}'", err=True)
    raise typer.Exit(code=1)


@app.command("match")
def match_cmd(
    text: str = typer.Argument(..., help="User intent phrasing to match against signal_phrases"),
    top: int = typer.Option(3, "--top", help="How many candidates to show"),
):
    """Rank archetypes by token overlap with the user's phrasing."""
    data = _load()
    user = _tokens(text)
    if not user:
        typer.echo("error: no meaningful tokens in input", err=True)
        raise typer.Exit(code=1)

    scored = [(_score(user, a), a) for a in data["archetypes"]]
    scored = [s for s in scored if s[0] > 0]
    scored.sort(key=lambda x: x[0], reverse=True)

    if not scored:
        typer.echo("no archetype matched. consider adding this shape to the registry.")
        raise typer.Exit(code=0)

    for score, a in scored[:top]:
        typer.echo(f"[{score}] {a['id']} — {a['name']}")
        typer.echo(_fmt_phases(a))
        typer.echo("")
