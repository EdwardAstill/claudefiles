"""Tests for `hooks/hook_types.py` — typed payload helpers.

The module lives in `hooks/` (co-located with the scripts that import it)
so pytest needs a `sys.path` tweak to reach it.
"""

import json
import sys
from pathlib import Path

# agentfiles repo root → .../hooks/ on sys.path.
_REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO_ROOT / "hooks"))

import hook_types  # noqa: E402


# ── Canonical-sample fixtures (sourced from hooks.md) ────────────────────────

_PRE_TOOL_USE_SAMPLE = {
    "session_id": "abc123",
    "transcript_path": "/home/u/.claude/projects/.../t.jsonl",
    "cwd": "/home/u/my-project",
    "permission_mode": "default",
    "hook_event_name": "PreToolUse",
    "tool_name": "Bash",
    "tool_input": {"command": "npm test"},
    "tool_use_id": "toolu_01ABC",
}

_POST_TOOL_USE_SAMPLE = {
    "session_id": "abc123",
    "transcript_path": "/home/u/.claude/projects/.../t.jsonl",
    "cwd": "/home/u/my-project",
    "permission_mode": "default",
    "hook_event_name": "PostToolUse",
    "tool_name": "Write",
    "tool_input": {"file_path": "/path/to/file.txt", "content": "x"},
    "tool_response": {"filePath": "/path/to/file.txt", "success": True},
    "tool_use_id": "toolu_01ABC",
}

_SESSION_START_SAMPLE = {
    "session_id": "abc123",
    "transcript_path": "/home/u/.claude/projects/.../t.jsonl",
    "cwd": "/home/u",
    "hook_event_name": "SessionStart",
    "source": "startup",
    "model": "claude-sonnet-4-6",
}

_USER_PROMPT_SAMPLE = {
    "session_id": "abc123",
    "cwd": "/home/u",
    "hook_event_name": "UserPromptSubmit",
    "prompt": "Write a factorial function",
}

_STOP_SAMPLE = {
    "session_id": "abc123",
    "cwd": "/home/u",
    "permission_mode": "default",
    "hook_event_name": "Stop",
}

_PERMISSION_REQUEST_SAMPLE = {
    "session_id": "abc123",
    "cwd": "/home/u",
    "hook_event_name": "PermissionRequest",
    "tool_name": "Bash",
    "tool_input": {"command": "rm -rf node_modules"},
}

_NOTIFICATION_SAMPLE = {
    "session_id": "abc123",
    "cwd": "/home/u",
    "hook_event_name": "Notification",
    "message": "Claude needs your permission to use Bash",
    "title": "Permission needed",
    "notification_type": "permission_prompt",
}


# ── parse() ──────────────────────────────────────────────────────────────────

def test_parse_pretooluse_from_json_string():
    payload = hook_types.parse("PreToolUse", json.dumps(_PRE_TOOL_USE_SAMPLE))
    assert payload["tool_name"] == "Bash"
    assert payload["tool_input"]["command"] == "npm test"
    assert payload["session_id"] == "abc123"


def test_parse_accepts_pre_parsed_dict():
    payload = hook_types.parse("PostToolUse", _POST_TOOL_USE_SAMPLE)
    assert payload["tool_name"] == "Write"
    assert payload["tool_response"]["success"] is True


def test_parse_all_seven_events_roundtrip():
    """Each documented event parses without raising and preserves fields."""
    samples = [
        ("SessionStart", _SESSION_START_SAMPLE, "source", "startup"),
        ("UserPromptSubmit", _USER_PROMPT_SAMPLE, "prompt", "Write a factorial function"),
        ("PreToolUse", _PRE_TOOL_USE_SAMPLE, "tool_name", "Bash"),
        ("PostToolUse", _POST_TOOL_USE_SAMPLE, "tool_name", "Write"),
        ("Stop", _STOP_SAMPLE, "hook_event_name", "Stop"),
        ("PermissionRequest", _PERMISSION_REQUEST_SAMPLE, "tool_name", "Bash"),
        ("Notification", _NOTIFICATION_SAMPLE, "notification_type", "permission_prompt"),
    ]
    for event, sample, field, expected in samples:
        payload = hook_types.parse(event, json.dumps(sample))
        assert payload[field] == expected, f"{event}: {field} mismatch"


def test_parse_malformed_json_returns_empty_dict():
    assert hook_types.parse("PreToolUse", "{not valid json") == {}
    assert hook_types.parse("PreToolUse", "") == {}


def test_parse_non_object_json_returns_empty_dict():
    # Top-level JSON that isn't an object (e.g. a bare array or string).
    assert hook_types.parse("PreToolUse", "[1, 2, 3]") == {}
    assert hook_types.parse("PreToolUse", '"just a string"') == {}


def test_parse_unknown_event_still_returns_data():
    """parse() should not reject events outside _EVENT_MAP — common fields
    still work for observability hooks."""
    raw = {"session_id": "x", "hook_event_name": "CwdChanged", "new_cwd": "/tmp"}
    payload = hook_types.parse("CwdChanged", json.dumps(raw))
    assert payload["session_id"] == "x"
    assert payload["new_cwd"] == "/tmp"


# ── tool_name() ──────────────────────────────────────────────────────────────

def test_tool_name_canonical_flat_shape():
    assert hook_types.tool_name({"tool_name": "Bash"}) == "Bash"


def test_tool_name_legacy_tool_key():
    # Older / custom payloads use `tool` instead of `tool_name`.
    assert hook_types.tool_name({"tool": "Read"}) == "Read"


def test_tool_name_missing_returns_none():
    assert hook_types.tool_name({}) is None
    assert hook_types.tool_name({"tool_name": ""}) is None


def test_tool_name_non_dict_returns_none():
    assert hook_types.tool_name("not a dict") is None  # type: ignore[arg-type]
    assert hook_types.tool_name(None) is None  # type: ignore[arg-type]


# ── bash_command() ───────────────────────────────────────────────────────────

def test_bash_command_canonical_nested_shape():
    payload = {"tool_input": {"command": "ls -la"}}
    assert hook_types.bash_command(payload) == "ls -la"


def test_bash_command_legacy_input_nesting():
    # Some older payloads nest under `input` instead of `tool_input`.
    payload = {"input": {"command": "echo hi"}}
    assert hook_types.bash_command(payload) == "echo hi"


def test_bash_command_flat_fallback():
    # Bare top-level `command` — the last-resort fallback.
    assert hook_types.bash_command({"command": "pwd"}) == "pwd"


def test_bash_command_missing_returns_none():
    assert hook_types.bash_command({}) is None
    assert hook_types.bash_command({"tool_input": {}}) is None
    assert hook_types.bash_command({"tool_input": {"command": ""}}) is None
