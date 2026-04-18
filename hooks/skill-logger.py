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

# Make the sibling `hooks/hook_types.py` importable. `uv run --script`
# doesn't add the script's directory to sys.path automatically, so we do
# it here. Named `hook_types` (not `types`) so it doesn't shadow the
# stdlib `types` module during import.
sys.path.insert(0, str(Path(__file__).parent))
import hook_types  # noqa: E402  (import after sys.path tweak)

SKILL_LOG = Path.home() / ".claude" / "logs" / "agentfiles.jsonl"
SESSION_LOG_DIR = Path.home() / ".claude" / "logs" / "sessions"
SESSION_STATE_DIR = Path.home() / ".claude" / "logs" / ".sessions"
SESSION_STATE_MAX_AGE_S = 60 * 60 * 24           # state files: 24h
SESSION_LOG_MAX_AGE_S = 60 * 60 * 24 * 7         # session JSONLs: 7 days
SKILL_LOG_MAX_BYTES = 5 * 1024 * 1024            # agentfiles.jsonl: 5 MB rolling
_CLEANUP_EVERY_N = 50                            # run rotation every ~50 invocations
_CLEANUP_MARKER = SESSION_STATE_DIR / ".last_cleanup"


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


def _should_run_cleanup() -> bool:
    """Throttle cleanup: only run if marker is missing or >1h old."""
    try:
        if not _CLEANUP_MARKER.exists():
            return True
        return (time.time() - _CLEANUP_MARKER.stat().st_mtime) > 3600
    except OSError:
        return False


def _touch_cleanup_marker() -> None:
    try:
        SESSION_STATE_DIR.mkdir(parents=True, exist_ok=True)
        _CLEANUP_MARKER.touch()
    except OSError:
        pass


def _cleanup_old_sessions() -> None:
    """Prune session state files (24h), session JSONL logs (7 days), and
    rotate the skill log if it exceeds SKILL_LOG_MAX_BYTES."""
    now = time.time()

    # 1. State files — 24h retention
    if SESSION_STATE_DIR.exists():
        state_cutoff = now - SESSION_STATE_MAX_AGE_S
        for f in SESSION_STATE_DIR.glob("*.json"):
            try:
                if f.stat().st_mtime < state_cutoff:
                    f.unlink(missing_ok=True)
            except OSError:
                pass

    # 2. Session JSONL logs — 7 day retention
    if SESSION_LOG_DIR.exists():
        log_cutoff = now - SESSION_LOG_MAX_AGE_S
        for f in SESSION_LOG_DIR.glob("session-*.jsonl"):
            try:
                if f.stat().st_mtime < log_cutoff:
                    f.unlink(missing_ok=True)
            except OSError:
                pass

    # 3. Skill log — size-based rotation, keep most recent half
    try:
        if SKILL_LOG.exists() and SKILL_LOG.stat().st_size > SKILL_LOG_MAX_BYTES:
            lines = SKILL_LOG.read_text().splitlines()
            keep = lines[len(lines) // 2:]
            SKILL_LOG.write_text("\n".join(keep) + ("\n" if keep else ""))
    except OSError:
        pass

    _touch_cleanup_marker()


def main():
    payload: hook_types.PostToolUsePayload = hook_types.parse(
        "PostToolUse", sys.stdin.read()
    )
    # Malformed / empty payload → parse() returned {} → bail out quietly.
    if not payload:
        sys.exit(0)

    # Resolve session ID — keep env-var fallback; it's a cross-process
    # channel, not part of the payload shape.
    session_id = (
        payload.get("session_id")
        or (payload.get("session", {}) or {}).get("id")
        or os.environ.get("CLAUDE_SESSION_ID", "")
        or "unknown"
    )

    # Resolve tool and input/output. Helper handles the flat-vs-nested
    # `tool_name`/`tool` variance; keep the `tool_input`/`input` and
    # `tool_output`/`output` fallback chains as-is for behavior parity.
    tool_name = hook_types.tool_name(payload) or ""
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    tool_output = payload.get("tool_output") or payload.get("output", "")

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
    if _should_run_cleanup():
        _cleanup_old_sessions()

    # Detect self-loop: skill invoking itself
    self_loop = skill_name == parent_skill

    # Track chain depth
    chain_depth = len(state["skills_seen"])

    entry = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "skill": skill_name,
        "session": session_id,
        "parent_skill": parent_skill,
        "escalated": escalated,
        "self_loop": self_loop,
        "chain_depth": chain_depth,
    }

    SKILL_LOG.parent.mkdir(parents=True, exist_ok=True)
    with SKILL_LOG.open("a") as f:
        f.write(json.dumps(entry) + "\n")

    sys.exit(0)


if __name__ == "__main__":
    main()
