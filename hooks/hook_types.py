"""Typed payload schemas for Claude Code hook events.

Zero-dependency module (stdlib only) that describes the JSON payloads our
hooks receive on stdin. Each event gets a `TypedDict` with `total=False`
since Claude Code payloads are permissive — fields may be absent, and new
upstream fields should never break us.

Import pattern (from sibling hook scripts under `hooks/`):

    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    import hook_types

NOTE: file is named `hook_types.py`, NOT `types.py`. Putting the hooks
directory on `sys.path` with a `types.py` in it shadows the stdlib
`types` module and breaks everything that imports `enum` (which pulls
`types`). The `hook_` prefix sidesteps that.

Shipped alongside `hooks/*.py` so scripts can resolve it without pulling
`tools/python/src/af/` into their script-run environment.

Schemas sourced from `research/documentation/claude-code/hooks.md`
(fetched 2026-04-18). Use `extra="allow"` semantics — we read known fields
but never reject unknown ones.
"""

from __future__ import annotations

import json
from typing import Any, TypedDict


# ── Base payload ─────────────────────────────────────────────────────────────
#
# Every hook event carries these common fields. Individual event TypedDicts
# extend this via inheritance.
class BasePayload(TypedDict, total=False):
    session_id: str
    transcript_path: str
    cwd: str
    permission_mode: str
    hook_event_name: str
    agent_id: str
    agent_type: str


# ── Per-event payloads ───────────────────────────────────────────────────────
class SessionStartPayload(BasePayload, total=False):
    source: str  # "startup" | "resume" | "clear" | "compact"
    model: str


class UserPromptSubmitPayload(BasePayload, total=False):
    prompt: str


class PreToolUsePayload(BasePayload, total=False):
    tool_name: str
    tool_input: dict[str, Any]
    tool_use_id: str


class PostToolUsePayload(BasePayload, total=False):
    tool_name: str
    tool_input: dict[str, Any]
    tool_response: dict[str, Any]
    tool_use_id: str


class StopPayload(BasePayload, total=False):
    # Stop carries only common fields per the canonical docs, but some
    # older or custom payloads include a stop_hook_active flag.
    stop_hook_active: bool


class PermissionRequestPayload(BasePayload, total=False):
    tool_name: str
    tool_input: dict[str, Any]
    permission_suggestions: list[dict[str, Any]]


class NotificationPayload(BasePayload, total=False):
    message: str
    title: str
    notification_type: str  # "permission_prompt" | "idle_prompt" | ...


# ── Event → TypedDict mapping ────────────────────────────────────────────────
# parse() keys off this to select the right shape. Unknown events still
# get a BasePayload so common-field access keeps working.
_EVENT_MAP: dict[str, type] = {
    "SessionStart": SessionStartPayload,
    "UserPromptSubmit": UserPromptSubmitPayload,
    "PreToolUse": PreToolUsePayload,
    "PostToolUse": PostToolUsePayload,
    "Stop": StopPayload,
    "PermissionRequest": PermissionRequestPayload,
    "Notification": NotificationPayload,
}


# ── parse() ──────────────────────────────────────────────────────────────────
def parse(event: str, raw: str | dict[str, Any]) -> dict[str, Any]:
    """Parse raw stdin JSON (or a pre-parsed dict) into a typed payload dict.

    Returns an empty dict on malformed input — NEVER raises. This preserves
    the exit-0 fail-safe posture every hook currently has: a broken payload
    means no-op, not error.

    The return value is typed as `dict[str, Any]` at runtime but matches
    one of the `*Payload` TypedDicts depending on `event`. Callers get
    static type safety by annotating the assignment:

        payload: PreToolUsePayload = parse("PreToolUse", raw)

    `event` selects the expected TypedDict shape. Unknown events fall
    through to BasePayload (common fields only). This matches the
    permissive spirit of Claude Code payloads.
    """
    if isinstance(raw, dict):
        data: dict[str, Any] = raw
    else:
        try:
            parsed = json.loads(raw)
        except (json.JSONDecodeError, ValueError, TypeError):
            return {}
        if not isinstance(parsed, dict):
            return {}
        data = parsed

    # No runtime validation beyond "is a dict" — TypedDict is a static
    # contract; actual payloads may carry extra fields and we keep them.
    # The _EVENT_MAP lookup is informational (confirms we know the event).
    _ = _EVENT_MAP.get(event)
    return data


# ── tool_name() ──────────────────────────────────────────────────────────────
def tool_name(payload: dict[str, Any]) -> str | None:
    """Extract the tool name across flat-vs-nested payload variants.

    Canonical shape is top-level `tool_name`, but we've seen older / custom
    payloads use `tool` as a fallback. Returns None if neither resolves to
    a non-empty string.
    """
    if not isinstance(payload, dict):
        return None
    name = payload.get("tool_name") or payload.get("tool")
    if isinstance(name, str) and name:
        return name
    return None


# ── bash_command() ───────────────────────────────────────────────────────────
def bash_command(payload: dict[str, Any]) -> str | None:
    """Extract the Bash `command` field for PreToolUse / PostToolUse payloads.

    Tries in order:
      1. payload['tool_input']['command']   (canonical)
      2. payload['input']['command']        (legacy nesting)
      3. payload['command']                 (flat fallback)

    Returns None if none resolve to a non-empty string.
    """
    if not isinstance(payload, dict):
        return None

    for container_key in ("tool_input", "input"):
        container = payload.get(container_key)
        if isinstance(container, dict):
            cmd = container.get("command")
            if isinstance(cmd, str) and cmd:
                return cmd

    cmd = payload.get("command")
    if isinstance(cmd, str) and cmd:
        return cmd
    return None


__all__ = [
    "BasePayload",
    "SessionStartPayload",
    "UserPromptSubmitPayload",
    "PreToolUsePayload",
    "PostToolUsePayload",
    "StopPayload",
    "PermissionRequestPayload",
    "NotificationPayload",
    "parse",
    "tool_name",
    "bash_command",
]
