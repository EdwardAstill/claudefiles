"""af metrics — one-shot dashboard aggregating scattered signals.

Pulls from: session logs, skill-invocation log, manifest audit, test suite,
anomaly log. Single-page summary for "how's the system doing?"
"""

from __future__ import annotations

import json
import subprocess
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

import typer

app = typer.Typer(help="Aggregate metrics dashboard.")

LOG_DIR = Path.home() / ".claude" / "logs"
SESSIONS_DIR = LOG_DIR / "sessions"
SKILL_LOG = LOG_DIR / "agentfiles.jsonl"
ANOMALIES = LOG_DIR / "anomalies.md"


def _load_skill_events() -> list[dict]:
    if not SKILL_LOG.is_file():
        return []
    out: list[dict] = []
    for line in SKILL_LOG.read_text().splitlines():
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return out


def _events_since(events: list[dict], days: int) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    out = []
    for e in events:
        try:
            t = datetime.fromisoformat(e["ts"].replace("Z", "+00:00"))
        except (KeyError, ValueError):
            continue
        if t >= cutoff:
            out.append(e)
    return out


@app.callback(invoke_without_command=True)
def metrics():
    """One-shot dashboard."""
    events = _load_skill_events()
    last7 = _events_since(events, 7)
    last30 = _events_since(events, 30)
    sessions7 = len({e.get("session") for e in last7 if e.get("session")})
    sessions30 = len({e.get("session") for e in last30 if e.get("session")})

    escalations7 = sum(1 for e in last7 if e.get("escalated"))
    top_skill_7 = Counter(e["skill"] for e in last7 if "skill" in e).most_common(1)
    top_name = top_skill_7[0][0] if top_skill_7 else "—"
    top_count = top_skill_7[0][1] if top_skill_7 else 0

    # Session file count
    recent_session_files = 0
    if SESSIONS_DIR.is_dir():
        cutoff = datetime.now().timestamp() - 7 * 86400
        recent_session_files = sum(
            1 for p in SESSIONS_DIR.glob("*.jsonl") if p.stat().st_mtime >= cutoff
        )

    # Anomaly count
    anomaly_count = 0
    if ANOMALIES.is_file() and ANOMALIES.stat().st_size > 0:
        anomaly_count = len([
            line for line in ANOMALIES.read_text().splitlines() if line.startswith("## ")
        ])

    # Audit status — shell out
    audit_status = "n/a"
    try:
        r = subprocess.run(
            ["af", "audit"], capture_output=True, text=True, timeout=10
        )
        last_line = [ln for ln in r.stdout.splitlines() if "SUMMARY:" in ln]
        audit_status = last_line[0].replace("SUMMARY: ", "").strip() if last_line else (
            "exit 0" if r.returncode == 0 else f"exit {r.returncode}"
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    typer.echo("# agentfiles metrics")
    typer.echo(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    typer.echo("")
    typer.echo("ACTIVITY")
    typer.echo(f"  last 7 days:   {len(last7):>4} skill loads across {sessions7} session(s)")
    typer.echo(f"  last 30 days:  {len(last30):>4} skill loads across {sessions30} session(s)")
    typer.echo(f"  session logs:  {recent_session_files:>4} file(s) in the last 7 days")
    typer.echo("")
    typer.echo("ROUTING HEALTH")
    typer.echo(f"  top skill (7d):   {top_name} ({top_count} loads)")
    typer.echo(f"  escalations (7d): {escalations7}")
    typer.echo(f"  anomalies:        {anomaly_count} unreviewed")
    typer.echo("")
    typer.echo("SYSTEM")
    typer.echo(f"  af audit:   {audit_status}")
