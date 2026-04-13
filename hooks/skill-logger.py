#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""PostToolUse skill logger — records SKILL.md reads to ~/.claude/logs/agentfiles.jsonl.

Each entry captures:
  ts            ISO 8601 UTC timestamp
  skill         skill directory name
  session       Claude Code session ID
  parent_skill  the skill that was active before this one in the session (proxy for caller)
  escalated     true if executor handed off to manager in this session
"""

import json
import sys
import os
import time
from datetime import datetime, timezone
from pathlib import Path

LOG_FILE = Path.home() / ".claude" / "logs" / "agentfiles.jsonl"
SESSION_DIR = Path.home() / ".claude" / "logs" / ".sessions"
SESSION_MAX_AGE_S = 60 * 60 * 24  # clean up session state older than 24 hours


def _session_file(session_id: str) -> Path:
    safe = session_id.replace("/", "_").replace("..", "_") or "unknown"
    return SESSION_DIR / f"{safe}.json"


def _load_session(session_id: str) -> dict:
    path = _session_file(session_id)
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {"last_skill": None, "skills_seen": [], "escalated": False}


def _save_session(session_id: str, state: dict) -> None:
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    _session_file(session_id).write_text(json.dumps(state))


def _cleanup_old_sessions() -> None:
    if not SESSION_DIR.exists():
        return
    cutoff = time.time() - SESSION_MAX_AGE_S
    for f in SESSION_DIR.glob("*.json"):
        try:
            if f.stat().st_mtime < cutoff:
                f.unlink(missing_ok=True)
        except OSError:
            pass


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    tool_name = data.get("tool_name", "") or data.get("tool", "")
    file_path = (
        data.get("tool_input", {}).get("file_path")
        or data.get("input", {}).get("file_path")
        or data.get("file_path")
        or ""
    )

    if tool_name != "Read":
        sys.exit(0)

    if not file_path.endswith("SKILL.md"):
        sys.exit(0)

    skill_name = Path(file_path).parent.name

    session_id = (
        data.get("session_id")
        or data.get("session", {}).get("id")
        or os.environ.get("CLAUDE_SESSION_ID", "")
        or "unknown"
    )

    # Load session state, update it, detect escalation
    state = _load_session(session_id)
    parent_skill = state["last_skill"]

    # Escalation: manager was loaded in a session where executor already ran
    if skill_name == "manager" and "executor" in state["skills_seen"]:
        state["escalated"] = True
    escalated = state["escalated"]

    state["last_skill"] = skill_name
    if skill_name not in state["skills_seen"]:
        state["skills_seen"].append(skill_name)

    _save_session(session_id, state)
    _cleanup_old_sessions()

    entry = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "skill": skill_name,
        "session": session_id,
        "parent_skill": parent_skill,
        "escalated": escalated,
    }

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a") as f:
        f.write(json.dumps(entry) + "\n")

    sys.exit(0)


if __name__ == "__main__":
    main()
