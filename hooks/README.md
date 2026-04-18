# agentfiles hooks

Claude Code (and Gemini CLI) fire lifecycle events. Each event runs the scripts
listed in `hooks.json`. A script reads a JSON payload from stdin and signals
back through its **exit code** (0 = pass, 2 = block, other = non-blocking
error) and, on exit 0, an optional JSON blob on **stdout** that can inject
context or alter tool behavior.

This directory is the source of truth for those scripts. `install.sh`
symlinks the whole directory into `~/.claude/skills/hooks` and
`~/.gemini/skills/hooks`, then `install-hooks.sh` / `install-gemini-hooks.sh`
merge the entries from `hooks.json` into `~/.claude/settings.json` /
`~/.gemini/settings.json`.

## Inventory

| Script              | Event(s)                                | Matcher  | Purpose                                                                                                                                            |
| ------------------- | --------------------------------------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `session-start`     | `SessionStart`                          | —        | Injects the `using-agentfiles` SKILL.md, pre-runs `af context` + `af status`, surfaces unreviewed routing anomalies. Emits `additionalContext`.    |
| `caveman-mode.py`   | `UserPromptSubmit`                      | —        | Re-injects caveman-mode reminder each turn if `~/.claude/caveman-mode` exists. Emits `additionalContext`.                                          |
| `safety-gate.py`    | `PreToolUse`                            | `Bash`   | Exits 2 on `rm -rf` outside a git worktree, force-push, `DROP TABLE`, fork bomb, `dd`, `mkfs`. Recoverable `rm -rf` inside a worktree is allowed.  |
| `skill-logger.py`   | `PostToolUse`                           | `.*`     | Writes every tool call to `~/.claude/logs/sessions/session-<id>.jsonl`. On SKILL.md reads, logs skill routing to `~/.claude/logs/agentfiles.jsonl`. Rotates logs. |
| `notify.py`         | `Stop`, `PermissionRequest`, `Notification` | —    | Desktop notifications via `notify-send`, per-session status files in `~/.claude/terminal-status/`, routing-anomaly detection on `Stop`. Async.     |
| `statusline.sh`     | (statusLine, not an event hook)         | —        | Renders the Claude Code statusline: cwd, git, model, context %, 5h usage, caveman tag.                                                             |

## Lifecycle events

Every payload includes `session_id`, `transcript_path`, `cwd`, `hook_event_name`.
Event-specific fields below are the ones we use; see
`/home/eastill/projects/agentfiles/research/documentation/claude-code/hooks.md`
for the full schema.

- **SessionStart** — `source` (`startup|resume|clear|compact`), `model`.
  Exit 0 + `{"hookSpecificOutput": {"hookEventName": "SessionStart",
  "additionalContext": "..."}}` injects context. Plain stdout also works. Exit
  2 is ignored (session already started).
- **UserPromptSubmit** — adds `prompt`. Exit 0 with `additionalContext`
  injects context; exit 2 erases the prompt and blocks.
- **PreToolUse** — adds `tool_name`, `tool_input`, `tool_use_id`. Exit 2
  **blocks the tool call** and feeds stderr back to Claude. This is the one
  place you can veto behavior.
- **PostToolUse** — adds `tool_name`, `tool_input`, `tool_response`. The
  tool already ran; exit 2 only surfaces stderr to Claude. Use for logging.
- **PermissionRequest** — adds `tool_name`, `tool_input`,
  `permission_suggestions`. Exit 2 denies; JSON `decision.behavior` can also
  `"allow"` with `updatedInput`/`updatedPermissions`.
- **Notification** — adds `message`, `title`, `notification_type`
  (`permission_prompt|idle_prompt|auth_success|elicitation_dialog`). Cannot
  block.
- **Stop** — minimal payload. Exit 2 keeps Claude running (rare). We use it
  for notifications and anomaly sweeps.

Exit code 1 is **not** a block anywhere. Use 2.

## Adding a new hook

1. **Pick the event** from the list above. If you need to veto, it has to be
   `PreToolUse`, `PermissionRequest`, `UserPromptSubmit`, `Stop`, or a
   `TaskCreated`/`TaskCompleted`.
2. **Write the script** next to the existing ones. Python goes through
   `uv run --script` so deps are declared inline and no venv management is
   needed. Follow the style of `caveman-mode.py:1-5` for the shebang +
   PEP 723 metadata block.
3. **Register in `hooks.json`** with `"command": "${CLAUDE_PLUGIN_ROOT}/hooks/your-hook.py"`.
   Add a `matcher` if the event supports one (PreToolUse, PostToolUse,
   PermissionRequest, Notification, SessionStart).
4. **Mirror into the installer.** Add the same entry to
   `install-hooks.sh` (for Claude) and, if relevant, `install-gemini-hooks.sh`.
   These are what write to `~/.claude/settings.json`.
5. **Re-run installation:**
   ```
   af install
   ```
   which invokes `install.sh` → symlinks the hooks dir → calls the two
   `install-*-hooks.sh` scripts. `--dry-run` is supported on all of them.

## Testing a hook

Hooks are plain scripts with JSON on stdin, so feed them synthetic input and
check the exit code and stdout. Use `subprocess.run` with `input=<json>` and
`capture_output=True`:

```python
import json, subprocess

payload = {
    "session_id": "test",
    "cwd": "/tmp",
    "hook_event_name": "PreToolUse",
    "tool_name": "Bash",
    "tool_input": {"command": "rm -rf /"},
}
r = subprocess.run(
    ["./safety-gate.py"],
    input=json.dumps(payload),
    capture_output=True, text=True, timeout=5,
)
assert r.returncode == 2, r.stderr
assert "BLOCKED" in r.stderr
```

Build a table of `(payload, expected_exit, expected_stderr_substr)` and loop
it. For context-injecting hooks, assert `r.returncode == 0` and
`json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]`.

## Style conventions (observed)

- **Python shebang:** `#!/usr/bin/env -S uv run --script` plus an inline
  `# /// script ... # ///` block declaring `requires-python` and
  `dependencies` (`safety-gate.py:1-5`, `notify.py:1-5`).
- **Parse defensively.** Wrap `json.load(sys.stdin)` in try/except and
  `sys.exit(0)` on malformed input — never propagate a parse error as an exit 2
  block (`safety-gate.py:79-82`, `skill-logger.py:115-118`).
- **Field fallbacks.** Claude Code and Gemini differ on field names; read both
  (`data.get("tool_name") or data.get("tool")`, `safety-gate.py:84`).
- **Block with `sys.exit(2)`** and a clear stderr line. The first line of
  stderr is what Claude/the user sees (`safety-gate.py:105-110`).
- **Inject context** via stdout JSON: `{"hookSpecificOutput": {"hookEventName":
  "<event>", "additionalContext": "..."}}` (`caveman-mode.py:61-67`,
  `session-start:63`).
- **`async: true`** for Stop/Notification/PermissionRequest hooks that do I/O
  (`hooks.json:51,63,73`) so the UI is not held up.

## Anti-patterns

- **Long-running hooks.** SessionStart and UserPromptSubmit hooks gate every
  session / prompt. Keep them under ~200ms on the happy path. No network calls
  without a `timeout=` (see the `timeout=3` in `safety-gate.py:55`).
- **Logging secrets.** `skill-logger.py` truncates tool output to 1000 chars
  (`_truncate`, line 32) but does not redact; don't add payload fields that
  contain API keys to the logged entry.
- **Using exit 1 to block.** Exit 1 is a non-blocking error everywhere except
  `WorktreeCreate`. Use 2.
- **Unbounded log growth.** If you append to a file, add a rotation path like
  `_cleanup_old_sessions` in `skill-logger.py:77-111`.
- **Forgetting the installer.** A hook that only lives in `hooks.json` but not
  in `install-hooks.sh` will work on this machine and silently break on a
  fresh install.
- **Blocking on I/O in Stop.** It delays the UI returning control. Run async
  or keep it trivial.
