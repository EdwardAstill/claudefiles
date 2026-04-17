#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Stop/Notification/PermissionRequest hook — terminal notifications + status tracking.

Sends desktop notifications via notify-send and writes per-session status to
~/.claude/terminal-status/ so `af hub` can display a live overview.

Events handled:
  Stop              → "Task complete" (normal urgency)
  PermissionRequest → "Needs approval: <tool>" (critical urgency)
  Notification      → "Waiting for input" when notification_type=idle_prompt (critical)
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

STATUS_DIR = Path.home() / ".claude" / "terminal-status"
SKILL_LOG = Path.home() / ".claude" / "logs" / "agentfiles.jsonl"
ANOMALIES_FILE = Path.home() / ".claude" / "logs" / "anomalies.md"


def detect_session_anomalies(session_id: str) -> list[str]:
    """Scan this session's skill log entries for routing anomalies."""
    if not SKILL_LOG.exists():
        return []
    anomalies: list[str] = []
    entries: list[dict] = []
    try:
        with SKILL_LOG.open() as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if e.get("session") == session_id:
                    entries.append(e)
    except OSError:
        return []

    if not entries:
        return []

    # Self-loops
    loops = [e for e in entries if e.get("self_loop")]
    if loops:
        names = sorted({e.get("skill", "?") for e in loops})
        anomalies.append(f"self-loop: {', '.join(names)}")

    # Chain depth > 3
    max_depth = max((e.get("chain_depth", 0) for e in entries), default=0)
    if max_depth > 3:
        chain = " → ".join(e.get("skill", "?") for e in entries[:max_depth + 1])
        anomalies.append(f"deep chain ({max_depth}): {chain}")

    # Wasted loads — same skill 3+ times
    from collections import Counter
    counts = Counter(e.get("skill") for e in entries)
    wasted = [s for s, c in counts.items() if c >= 3 and s]
    if wasted:
        anomalies.append(f"wasted loads (≥3x): {', '.join(wasted)}")

    return anomalies


def record_anomalies(session_id: str, cwd: str, anomalies: list[str]) -> None:
    """Append anomalies to a rolling markdown log for manual review."""
    if not anomalies:
        return
    ANOMALIES_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry = [f"## {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}  ·  {cwd or '?'}",
             f"session: `{session_id}`", ""]
    entry += [f"- {a}" for a in anomalies]
    entry.append("")
    with ANOMALIES_FILE.open("a") as f:
        f.write("\n".join(entry) + "\n")


def notify(summary: str, body: str, urgency: str = "normal") -> None:
    subprocess.run(
        ["notify-send", "-u", urgency, "-a", "Claude Code", summary, body],
        capture_output=True,
    )


def write_status(session_id: str, state: str, cwd: str, extra: dict | None = None) -> None:
    STATUS_DIR.mkdir(parents=True, exist_ok=True)
    status = {
        "session_id": session_id,
        "state": state,
        "ts": datetime.now(timezone.utc).isoformat(),
        "cwd": cwd,
        "wezterm_pane": os.environ.get("WEZTERM_PANE", ""),
        **(extra or {}),
    }
    (STATUS_DIR / f"{session_id}.json").write_text(json.dumps(status, indent=2))


def short_path(cwd: str) -> str:
    if not cwd:
        return "unknown"
    p = Path(cwd)
    # Show last two path segments for context (e.g. projects/myapp)
    parts = p.parts
    return "/".join(parts[-2:]) if len(parts) >= 2 else p.name


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    event = data.get("hook_event_name", "")
    session_id = data.get("session_id", "unknown")
    cwd = data.get("cwd", "")
    label = short_path(cwd)

    if event == "Stop":
        write_status(session_id, "idle", cwd)
        notify("Claude Code", f"Done — {label}")
        anomalies = detect_session_anomalies(session_id)
        if anomalies:
            record_anomalies(session_id, cwd, anomalies)
            notify(
                "Claude Code — routing anomalies",
                " · ".join(anomalies)[:200],
                urgency="low",
            )

    elif event == "PermissionRequest":
        tool = data.get("tool_name", "unknown tool")
        write_status(session_id, "needs_approval", cwd, {"tool": tool})
        notify("Claude Code — Needs Approval", f"{tool}  ·  {label}", urgency="critical")

    elif event == "Notification":
        if data.get("notification_type") == "idle_prompt":
            write_status(session_id, "waiting_input", cwd)
            notify("Claude Code — Waiting", f"Needs input  ·  {label}", urgency="critical")

    sys.exit(0)


if __name__ == "__main__":
    main()
