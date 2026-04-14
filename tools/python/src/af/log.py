"""af log — show skill invocation log and session traces."""

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import typer

app = typer.Typer(help="Show skill invocation log.")

LOG_FILE = Path.home() / ".claude" / "logs" / "agentfiles.jsonl"
SESSION_LOG_DIR = Path.home() / ".claude" / "logs" / "sessions"


def _read_entries(skill: Optional[str] = None, escalations_only: bool = False) -> list[dict]:
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
            if escalations_only and not entry.get("escalated"):
                continue
            entries.append(entry)
    return entries


def _has_extended_fields(entries: list[dict]) -> bool:
    return any("parent_skill" in e for e in entries)


def _get_latest_session_file() -> Optional[Path]:
    if not SESSION_LOG_DIR.exists():
        return None
    files = sorted(SESSION_LOG_DIR.glob("session-*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True)
    return files[0] if files else None


@app.command()
def session(
    id: Optional[str] = typer.Option(None, "--id", help="Session ID (default: latest)."),
):
    """Show a condensed timeline of tool calls for a specific session."""
    if id:
        session_file = SESSION_LOG_DIR / f"session-{id}.jsonl"
    else:
        session_file = _get_latest_session_file()

    if not session_file or not session_file.exists():
        typer.echo(f"No session log found for {'ID ' + id if id else 'latest session'}.")
        return

    typer.echo(f"TIMELINE: {session_file.name}")
    typer.echo("-" * 60)

    with session_file.open() as f:
        for line in f:
            try:
                entry = json.loads(line)
                ts = entry.get("ts", "").split("T")[-1].replace("Z", "")
                tool = entry.get("tool", "")

                # Format specific tool inputs for readability
                input_data = entry.get("input", {})
                desc = ""
                if tool in ("run_shell_command", "Bash"):
                    desc = f": {input_data.get('command', '')}"
                elif tool in ("Read", "Edit", "Write", "replace"):
                    desc = f": {input_data.get('file_path', '')}"

                typer.echo(f"[{ts}] {tool}{desc}")
            except (json.JSONDecodeError, KeyError):
                continue


@app.command()
def analyze(
    id: Optional[str] = typer.Option(None, "--id", help="Session ID (default: latest)."),
):
    """Analyze a session for recovery patterns and lessons learned."""
    if id:
        session_file = SESSION_LOG_DIR / f"session-{id}.jsonl"
    else:
        session_file = _get_latest_session_file()

    if not session_file or not session_file.exists():
        typer.echo("No session log found to analyze.")
        return

    typer.echo(f"ANALYSIS: {session_file.name}")
    typer.echo("-" * 60)

    history = []
    with session_file.open() as f:
        for line in f:
            try:
                history.append(json.loads(line))
            except (json.JSONDecodeError, KeyError):
                continue

    # Detection: Failed command -> Success pattern
    failures = []
    for i, entry in enumerate(history):
        if entry.get("tool") in ("run_shell_command", "Bash"):
            output = str(entry.get("output", ""))
            if "FAILED" in output.upper() or "ERROR" in output.upper():
                failures.append(i)

    if failures:
        typer.echo("Recovery patterns:")
        for idx in failures:
            fail_entry = history[idx]
            cmd = fail_entry.get("input", {}).get("command", "")
            typer.echo(f"  - Failed: {cmd}")
            # Look for subsequent success on same or related command
            for j in range(idx + 1, min(idx + 10, len(history))):
                succ_entry = history[j]
                if succ_entry.get("tool") in ("run_shell_command", "Bash"):
                    s_out = str(succ_entry.get("output", ""))
                    if "error" not in s_out.lower() and "FAILED" not in s_out.upper():
                        s_cmd = succ_entry.get("input", {}).get("command", "")
                        typer.echo(f"    -> Resolved by: {s_cmd}")
                        break
    else:
        typer.echo("No obvious command failures detected.")


def _read_session_entries(session_file: Path) -> list[dict]:
    """Read all entries from a session trace file."""
    entries = []
    with session_file.open() as f:
        for line in f:
            try:
                entries.append(json.loads(line))
            except (json.JSONDecodeError, KeyError):
                continue
    return entries


def _find_recovery_patterns(history: list[dict]) -> list[dict]:
    """Find failed-command -> fix -> success patterns in a session."""
    patterns = []
    for i, entry in enumerate(history):
        if entry.get("tool") not in ("run_shell_command", "Bash"):
            continue
        output = str(entry.get("output", ""))
        if "FAILED" not in output.upper() and "ERROR" not in output.upper():
            continue
        failed_cmd = entry.get("input", {}).get("command", "")
        # Look for edits and subsequent success
        edits = []
        resolved_by = None
        for j in range(i + 1, min(i + 15, len(history))):
            later = history[j]
            tool = later.get("tool", "")
            if tool in ("Edit", "Write", "replace"):
                edits.append(later.get("input", {}).get("file_path", ""))
            elif tool in ("run_shell_command", "Bash"):
                s_out = str(later.get("output", ""))
                if "error" not in s_out.lower() and "FAILED" not in s_out.upper():
                    resolved_by = later.get("input", {}).get("command", "")
                    break
        patterns.append({
            "failed_cmd": failed_cmd,
            "files_edited": list(dict.fromkeys(edits)),  # dedupe preserving order
            "resolved_by": resolved_by,
        })
    return patterns


def _find_wasted_skill_loads(history: list[dict]) -> list[str]:
    """Find skills that were loaded (Read SKILL.md) but whose domain tools were never used."""
    loaded_skills = []
    for entry in history:
        if entry.get("tool") == "Read":
            fp = entry.get("input", {}).get("file_path", "")
            if fp.endswith("SKILL.md"):
                loaded_skills.append(Path(fp).parent.name)
    # A skill is "wasted" if it was loaded but the session had <3 tool calls after it
    # before another skill was loaded. Simple heuristic: if a skill appears only once
    # and the session is long, it's probably fine. Flag duplicates (loaded multiple times).
    counts = Counter(loaded_skills)
    return [name for name, count in counts.items() if count >= 3]


@app.command()
def review(
    keep_stats: bool = typer.Option(False, "--keep-stats", help="Don't clear agentfiles.jsonl after review."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print summary but don't clear logs or write observations."),
):
    """Review accumulated logs, surface patterns, append to observations.md, and clear session traces."""
    observations_file = Path.home() / ".claude" / "logs" / "observations.md"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    lines: list[str] = []
    has_content = False

    # --- Skill usage stats ---
    entries = _read_entries()
    # Filter out category routers (not real skill invocations)
    _CATEGORY_NAMES = {"coding", "management", "meta", "planning", "quality", "research", "skills"}
    entries = [e for e in entries if e.get("skill") not in _CATEGORY_NAMES]
    if entries:
        has_content = True
        counts = Counter(e.get("skill", "<unknown>") for e in entries)
        n_escalations = sum(1 for e in entries if e.get("escalated"))
        total = len(entries)
        unique = len(counts)

        lines.append(f"## Review — {now}")
        lines.append("")
        lines.append(f"**{total} skill invocations** across {unique} skills, {n_escalations} escalations")
        lines.append("")

        # Low-usage skills (candidates for deletion/merge)
        low_usage = [(name, count) for name, count in counts.most_common() if count <= 2]
        if low_usage:
            lines.append("**Low-usage skills** (<=2 invocations — delete or merge?):")
            for name, count in low_usage:
                lines.append(f"- `{name}` ({count})")
            lines.append("")

        # Escalation details
        if n_escalations > 0:
            esc_rate = n_escalations / total * 100
            lines.append(f"**Escalation rate:** {esc_rate:.1f}% ({n_escalations}/{total})")
            if esc_rate > 5:
                lines.append("  ⚠ Above 5% threshold — review executor routing")
            lines.append("")

        # Top skills
        lines.append("**Top skills:**")
        for name, count in counts.most_common(10):
            lines.append(f"- `{name}` ({count})")
        lines.append("")

    # --- Session trace analysis ---
    session_files = sorted(SESSION_LOG_DIR.glob("session-*.jsonl"), key=lambda f: f.stat().st_mtime) if SESSION_LOG_DIR.exists() else []

    all_recovery_patterns: list[dict] = []
    reloaded_skills: list[str] = []

    for sf in session_files:
        history = _read_session_entries(sf)
        all_recovery_patterns.extend(_find_recovery_patterns(history))
        reloaded_skills.extend(_find_wasted_skill_loads(history))

    if all_recovery_patterns:
        has_content = True
        lines.append(f"**Recovery patterns** (across {len(session_files)} sessions):")
        for p in all_recovery_patterns:
            failed = p["failed_cmd"]
            # Truncate long commands
            if len(failed) > 80:
                failed = failed[:77] + "..."
            line = f"- Failed: `{failed}`"
            if p["files_edited"]:
                edited = ", ".join(f"`{Path(f).name}`" for f in p["files_edited"][:3])
                line += f" → edited {edited}"
            if p["resolved_by"]:
                resolved = p["resolved_by"]
                if len(resolved) > 60:
                    resolved = resolved[:57] + "..."
                line += f" → resolved: `{resolved}`"
            lines.append(line)
        lines.append("")

    if reloaded_skills:
        has_content = True
        lines.append("**Skills loaded 3+ times in a single session** (context churn?):")
        for name in sorted(set(reloaded_skills)):
            lines.append(f"- `{name}`")
        lines.append("")

    if not has_content:
        typer.echo("No logs to review. Nothing to do.")
        return

    summary = "\n".join(lines)

    # Print summary
    typer.echo(summary)
    typer.echo("-" * 60)

    if dry_run:
        typer.echo("[dry-run] Would append above to observations.md and clear session traces.")
        return

    # Append to observations.md
    observations_file.parent.mkdir(parents=True, exist_ok=True)
    with observations_file.open("a") as f:
        f.write("\n" + summary + "\n")
    typer.echo(f"Appended to {observations_file}")

    # Clear session traces
    cleared = 0
    for sf in session_files:
        sf.unlink(missing_ok=True)
        cleared += 1
    if cleared:
        typer.echo(f"Cleared {cleared} session trace(s).")

    # Clear skill invocation log unless --keep-stats
    if not keep_stats and LOG_FILE.exists():
        LOG_FILE.unlink()
        typer.echo("Cleared agentfiles.jsonl (use --keep-stats to keep).")


@app.callback(invoke_without_command=True)
def log(
    ctx: typer.Context,
    skill: Optional[str] = typer.Option(None, "--skill", "-s", help="Filter to a specific skill name."),
    stats: bool = typer.Option(False, "--stats", help="Show frequency table sorted by invocation count."),
    escalations: bool = typer.Option(False, "--escalations", "-e", help="Show only sessions where executor escalated to manager."),
    tail: int = typer.Option(20, "--tail", "-n", help="Show last N entries (default: 20)."),
):
    """Show skill invocation log from ~/.claude/logs/agentfiles.jsonl."""
    if ctx.invoked_subcommand is not None:
        return

    entries = _read_entries(skill=skill, escalations_only=escalations)

    if not entries:
        if not LOG_FILE.exists():
            typer.echo("No log yet. Skills are logged when invoked.")
        else:
            filter_msg = f" for skill '{skill}'" if skill else ""
            filter_msg += " (escalations only)" if escalations else ""
            typer.echo(f"No log entries found{filter_msg}.")
        return

    if stats:
        counts = Counter(e.get("skill", "<unknown>") for e in entries)
        typer.echo(f"{'skill':<30}  {'count':>6}")
        typer.echo("-" * 40)
        for skill_name, count in counts.most_common():
            typer.echo(f"{skill_name:<30}  {count:>6}")
        n_escalations = sum(1 for e in entries if e.get("escalated"))
        typer.echo(f"\nTotal: {len(entries)} invocations, {len(counts)} unique skills, {n_escalations} escalations")
        return

    shown = entries[-tail:]
    extended = _has_extended_fields(shown)

    if extended:
        typer.echo(f"{'timestamp':<22}  {'skill':<28}  {'called by':<20}  {'esc'}")
        typer.echo("-" * 80)
        for entry in shown:
            ts = entry.get("ts", "")
            skill_name = entry.get("skill", "<unknown>")
            parent = entry.get("parent_skill") or "-"
            esc = "[!]" if entry.get("escalated") else ""
            typer.echo(f"{ts:<22}  {skill_name:<28}  {parent:<20}  {esc}")
    else:
        typer.echo(f"{'timestamp':<22}  {'skill'}")
        typer.echo("-" * 50)
        for entry in shown:
            ts = entry.get("ts", "")
            skill_name = entry.get("skill", "<unknown>")
            typer.echo(f"{ts:<22}  {skill_name}")

    if len(entries) > tail:
        typer.echo(f"\n(showing last {tail} of {len(entries)} entries — use --tail N to see more)")
