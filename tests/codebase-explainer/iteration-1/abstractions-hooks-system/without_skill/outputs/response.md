# Core Abstractions of the Hooks System

The `hooks/` directory is a set of Python scripts and a registration JSON that extend Claude Code via its hook events. The conceptual spine:

## 1. Typed hook payloads (`hook_types.py`)

A set of TypedDicts (BasePayload + per-event variants like PreToolUsePayload, PostToolUsePayload, etc.) plus helper functions `parse(event, raw)`, `tool_name(payload)`, `bash_command(payload)`. These let hook scripts read stdin with a known shape. The file is explicitly named `hook_types.py` (not `types.py`) to avoid shadowing the stdlib. Consumers: `skill-logger.py`, `safety-gate.py`, `modes.py`, `notify.py` — all call `hook_types.parse()` at the top of main().

## 2. Hook registration (`hooks.json`)

JSON declaring which script runs on which event, with optional matchers. Top-level is a `hooks` map keyed by event name (SessionStart, UserPromptSubmit, PreToolUse, PostToolUse, Stop, PermissionRequest, Notification). Each value is a list of entries like `{"matcher": "Bash", "hooks": [{"type": "command", "command": "..."}]}`. Interpolation of `${CLAUDE_PLUGIN_ROOT}` happens at install time. Consumers: `install-hooks.sh`, `install-gemini-hooks.sh`, Claude Code runtime.

## 3. Hook script convention

Every script under `hooks/` is an executable with the same shape: shebang (`uv run --script` with inline deps), read JSON from stdin, parse via `hook_types.parse`, do its side effect, exit 0 or non-zero. Consumers: the Claude Code runtime invokes them; hooks.json names them.

## 4. Logging pipeline (`skill-logger.py`)

PostToolUse hook that writes two logs: `~/.claude/logs/sessions/session-<id>.jsonl` (all tool calls with inputs and truncated outputs) and `~/.claude/logs/agentfiles.jsonl` (SKILL.md reads with escalation + self-loop detection). Also maintains per-session state in `~/.claude/logs/.sessions/`. Rotation by size for the skill log, by age for session state. Consumers: `af log`, `af skill-usage`, `af metrics`, `af learn`.

## 5. Safety / mode gates

`safety-gate.py` (PreToolUse Bash matcher — can block a command by exiting non-zero) and `modes.py` (UserPromptSubmit — enforces behavioral modes). Purpose: policy layer over tool calls and prompt shaping. Consumers: Claude Code runtime; `af mode` toggles state that modes.py reads.

## Summary

These five abstractions together define the hooks spine: types for the messages, JSON for the wiring, a script convention for the hooks themselves, a logging pipeline for observability, and safety/mode gates for policy.
