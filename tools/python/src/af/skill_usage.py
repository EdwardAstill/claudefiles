"""af skill-usage — telemetry over the agentfiles skill-invocation log.

Reads `~/.claude/logs/agentfiles.jsonl` (one line per skill load) and reports
ranked tables: most-loaded, cold-loaded, child-skill dispatch chains, and
escalation-rate. Input for pruning the catalog and picking skills to test.

The log schema (written by hooks/skill-logger.py):
  {"ts": ISO8601, "skill": NAME, "session": SESSION_ID,
   "parent_skill": NAME|null, "escalated": bool}
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import typer

app = typer.Typer(help="Skill usage telemetry.")

LOG = Path.home() / ".claude" / "logs" / "agentfiles.jsonl"


def _load_events() -> list[dict]:
    if not LOG.is_file():
        typer.echo(f"error: no log at {LOG}", err=True)
        raise typer.Exit(code=2)
    events: list[dict] = []
    for line in LOG.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def _discover_catalog_skills() -> set[str]:
    """Return skill names declared on disk in the repo, if we can find one."""
    candidates = [
        Path.cwd() / "agentfiles",
        Path.home() / "projects" / "agentfiles" / "agentfiles",
    ]
    root = next((c for c in candidates if c.is_dir()), None)
    if root is None:
        return set()
    names: set[str] = set()
    for skill_md in root.rglob("SKILL.md"):
        if "agents" in skill_md.parent.parts:
            continue
        for line in skill_md.read_text().splitlines():
            if line.startswith("name:"):
                names.add(line.split(":", 1)[1].strip())
                break
    return names


def _filter_agentfiles(events: list[dict], catalog: set[str]) -> list[dict]:
    """Strip events whose skill name isn't in the agentfiles catalog."""
    if not catalog:
        return events
    return [e for e in events if e.get("skill") in catalog]


@app.command("summary")
def summary_cmd(
    days: int = typer.Option(30, "--days", "-d", help="Only include events from the last N days"),
    top: int = typer.Option(20, "--top", "-n", help="How many rows per table"),
    include_external: bool = typer.Option(False, "--include-external", help="Include skills not in the agentfiles catalog (noise from other projects)"),
):
    """Ranked tables: most-loaded, cold-loaded, top parent→child chains."""
    events = _load_events()
    catalog = _discover_catalog_skills()
    if catalog and not include_external:
        events = _filter_agentfiles(events, catalog)
    cutoff = None
    if days > 0:
        cutoff = datetime.now(timezone.utc).timestamp() - days * 86400

    filtered: list[dict] = []
    for e in events:
        ts = e.get("ts", "")
        try:
            t = datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
        except ValueError:
            continue
        if cutoff is None or t >= cutoff:
            filtered.append(e)

    if not filtered:
        typer.echo(f"(no events in the last {days} day(s))")
        return

    loads = Counter(e["skill"] for e in filtered if "skill" in e)
    escalations = Counter(e["skill"] for e in filtered if e.get("escalated"))
    chains: Counter[tuple[str, str]] = Counter()
    for e in filtered:
        parent = e.get("parent_skill")
        child = e.get("skill")
        if parent and child:
            chains[(parent, child)] += 1

    sessions = set(e.get("session") for e in filtered if e.get("session"))

    typer.echo(f"Events: {len(filtered)}  |  Sessions: {len(sessions)}  |  Window: last {days} day(s)")
    typer.echo("")

    typer.echo(f"MOST LOADED (top {top})")
    for name, count in loads.most_common(top):
        esc = escalations.get(name, 0)
        esc_col = f"esc={esc}" if esc else ""
        typer.echo(f"  {count:>4}  {name:<35}  {esc_col}")

    catalog = _discover_catalog_skills()
    if catalog:
        loaded_names = set(loads)
        cold = sorted(catalog - loaded_names)
        typer.echo("")
        typer.echo(f"NEVER LOADED ({len(cold)} of {len(catalog)} in catalog)")
        if cold:
            for name in cold[:top]:
                typer.echo(f"        {name}")
            if len(cold) > top:
                typer.echo(f"        ... and {len(cold) - top} more")

    typer.echo("")
    typer.echo(f"TOP DISPATCH CHAINS (top {top})")
    for (parent, child), count in chains.most_common(top):
        typer.echo(f"  {count:>4}  {parent}  →  {child}")


@app.command("rank")
def rank_cmd(
    days: int = typer.Option(30, "--days", "-d"),
):
    """TSV rank of every loaded skill — pipeable into skill-tester or fzf."""
    events = _load_events()
    cutoff = None
    if days > 0:
        cutoff = datetime.now(timezone.utc).timestamp() - days * 86400
    loads = Counter()
    for e in events:
        ts = e.get("ts", "")
        try:
            t = datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
        except ValueError:
            continue
        if cutoff is None or t >= cutoff:
            if "skill" in e:
                loads[e["skill"]] += 1
    for name, count in loads.most_common():
        typer.echo(f"{count}\t{name}")


@app.command("sessions")
def sessions_cmd(skill: str = typer.Argument(..., help="Skill name")):
    """Show session IDs where a given skill was loaded, newest first."""
    events = _load_events()
    rows = [(e.get("ts", ""), e.get("session", "")) for e in events if e.get("skill") == skill]
    rows.sort(reverse=True)
    seen: set[str] = set()
    for ts, sid in rows:
        if sid in seen or not sid:
            continue
        seen.add(sid)
        typer.echo(f"{ts}\t{sid}")
