#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""PostToolUse logger — two layers of logging:

1. Session trace: ALL tool calls → ~/.claude/logs/sessions/session-<id>.jsonl
   (inputs, truncated outputs, timestamps — for post-session analysis)

2. Skill invocation log: SKILL.md reads → ~/.claude/logs/agentfiles.jsonl
   (skill name, parent_skill, escalation detection — for monthly review)
"""

import json
import sys
import os
import time
from datetime import datetime, timezone
from pathlib import Path

SKILL_LOG = Path.home() / ".claude" / "logs" / "agentfiles.jsonl"
SESSION_LOG_DIR = Path.home() / ".claude" / "logs" / "sessions"
SESSION_STATE_DIR = Path.home() / ".claude" / "logs" / ".sessions"
SESSION_MAX_AGE_S = 60 * 60 * 24  # clean up session state older than 24 hours


def _truncate(data, max_len=1000):
    """Truncate tool output to keep log files manageable."""
    if isinstance(data, str) and len(data) > max_len:
        return data[:max_len] + "... [truncated]"
    return data


def _session_state_file(session_id: str) -> Path:
    safe = session_id.replace("/", "_").replace("..", "_") or "unknown"
    return SESSION_STATE_DIR / f"{safe}.json"


def _load_session_state(session_id: str) -> dict:
    path = _session_state_file(session_id)
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {"last_skill": None, "skills_seen": [], "escalated": False}


def _save_session_state(session_id: str, state: dict) -> None:
    SESSION_STATE_DIR.mkdir(parents=True, exist_ok=True)
    _session_state_file(session_id).write_text(json.dumps(state))


def _cleanup_old_sessions() -> None:
    if not SESSION_STATE_DIR.exists():
        return
    cutoff = time.time() - SESSION_MAX_AGE_S
    for f in SESSION_STATE_DIR.glob("*.json"):
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

    # Resolve session ID
    session_id = (
        data.get("session_id")
        or data.get("session", {}).get("id")
        or os.environ.get("CLAUDE_SESSION_ID", "")
        or "unknown"
    )

    # Resolve tool and input/output
    tool_name = data.get("tool_name", "") or data.get("tool", "")
    tool_input = data.get("tool_input") or data.get("input", {})
    tool_output = data.get("tool_output") or data.get("output", "")

    # --- Layer 1: Session trace (all tool calls) ---
    session_entry = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "session": session_id,
        "tool": tool_name,
        "input": tool_input,
        "output": _truncate(tool_output),
    }

    SESSION_LOG_DIR.mkdir(parents=True, exist_ok=True)
    session_file = SESSION_LOG_DIR / f"session-{session_id}.jsonl"
    with session_file.open("a") as f:
        f.write(json.dumps(session_entry) + "\n")

    # --- Layer 2: Skill invocation log (only SKILL.md reads) ---
    if tool_name != "Read":
        sys.exit(0)

    file_path = tool_input.get("file_path", "")
    if not file_path.endswith("SKILL.md"):
        sys.exit(0)

    skill_dir = Path(file_path).parent
    skill_name = skill_dir.name

    # Skip category routers (directories that contain child SKILL.md files)
    child_skills = list(skill_dir.glob("*/SKILL.md"))
    if child_skills:
        sys.exit(0)

    # Load session state, update it, detect escalation
    state = _load_session_state(session_id)
    parent_skill = state["last_skill"]

    # Escalation: manager was loaded in a session where executor already ran
    if skill_name == "manager" and "executor" in state["skills_seen"]:
        state["escalated"] = True
    escalated = state["escalated"]

    state["last_skill"] = skill_name
    if skill_name not in state["skills_seen"]:
        state["skills_seen"].append(skill_name)

    _save_session_state(session_id, state)
    _cleanup_old_sessions()

    entry = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "skill": skill_name,
        "session": session_id,
        "parent_skill": parent_skill,
        "escalated": escalated,
    }

    SKILL_LOG.parent.mkdir(parents=True, exist_ok=True)
    with SKILL_LOG.open("a") as f:
        f.write(json.dumps(entry) + "\n")

    sys.exit(0)


if __name__ == "__main__":
    main()
