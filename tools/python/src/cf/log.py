"""cf log — show skill invocation log."""

import json
from collections import Counter
from pathlib import Path
from typing import Optional

import typer

app = typer.Typer(help="Show skill invocation log.")

LOG_FILE = Path.home() / ".claude" / "logs" / "claudefiles.jsonl"


def _read_entries(skill: Optional[str] = None) -> list[dict]:
    if not LOG_FILE.exists():
        return []
    entries = []
    with LOG_FILE.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if skill and entry.get("skill") != skill:
                continue
            entries.append(entry)
    return entries


@app.callback(invoke_without_command=True)
def log(
    ctx: typer.Context,
    skill: Optional[str] = typer.Option(None, "--skill", "-s", help="Filter to a specific skill name."),
    stats: bool = typer.Option(False, "--stats", help="Show frequency table sorted by invocation count."),
    tail: int = typer.Option(20, "--tail", "-n", help="Show last N entries (default: 20)."),
):
    """Show skill invocation log from ~/.claude/logs/claudefiles.jsonl."""
    if ctx.invoked_subcommand is not None:
        return

    entries = _read_entries(skill=skill)

    if not entries:
        if not LOG_FILE.exists():
            typer.echo("No log yet. Skills are logged when invoked.")
        else:
            filter_msg = f" for skill '{skill}'" if skill else ""
            typer.echo(f"No log entries found{filter_msg}.")
        return

    if stats:
        counts = Counter(e.get("skill", "<unknown>") for e in entries)
        typer.echo(f"{'skill':<30}  {'count':>6}")
        typer.echo("-" * 40)
        for skill_name, count in counts.most_common():
            typer.echo(f"{skill_name:<30}  {count:>6}")
        typer.echo(f"\nTotal: {len(entries)} invocations, {len(counts)} unique skills")
        return

    # Default: show last N entries as table
    shown = entries[-tail:]
    typer.echo(f"{'timestamp':<22}  {'skill'}")
    typer.echo("-" * 50)
    for entry in shown:
        ts = entry.get("ts", "")
        skill_name = entry.get("skill", "<unknown>")
        typer.echo(f"{ts:<22}  {skill_name}")

    if len(entries) > tail:
        typer.echo(f"\n(showing last {tail} of {len(entries)} entries — use --tail N to see more)")
