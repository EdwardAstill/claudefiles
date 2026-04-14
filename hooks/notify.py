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
