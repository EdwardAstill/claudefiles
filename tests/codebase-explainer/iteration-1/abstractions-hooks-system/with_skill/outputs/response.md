# Core Abstractions of the `hooks/` System

## Step 1 — Orient

The `hooks/` directory contains executable Python scripts, a registration JSON, installer scripts, and a typed payload module. It bridges Claude Code's hook events to agentfiles' own observability and policy layers. Top-level layout:

- `hook_types.py` — shared type schemas
- `hooks.json` — declarative wiring
- Hook scripts: `skill-logger.py`, `safety-gate.py`, `modes.py`, `notify.py`, `session-start`
- Installers: `install-hooks.sh`, `install-gemini-hooks.sh`
- Tests: `hooks/tests/`
- Docs: `hooks/README.md`

## Step 2 — The Conceptual Spine: 5 Abstractions

### Abstraction 1 — Typed Payload Schemas

**Defines:** `hooks/hook_types.py`
**Shape:**
- TypedDicts: `BasePayload` (session_id, transcript_path, cwd, permission_mode, hook_event_name, agent_id, agent_type), extended by `SessionStartPayload`, `UserPromptSubmitPayload`, `PreToolUsePayload`, `PostToolUsePayload`, `StopPayload`, `PermissionRequestPayload`, `NotificationPayload`. All `total=False` — payloads are permissive by design.
- Module helpers: `parse(event, raw) -> dict` (returns `{}` on any error — NEVER raises; enforces the fail-safe exit-0 posture), `tool_name(payload)` (flat-vs-nested fallback: `tool_name` > `tool`), `bash_command(payload)` (container chain: `tool_input.command` > `input.command` > `command`).
- Event→TypedDict mapping (`_EVENT_MAP`).

**What it's FOR:** A stable, typed contract for JSON stdin so hook scripts don't do ad-hoc field access. The TypedDict approach is static-only; runtime stays permissive (extra fields preserved). The file name `hook_types.py` avoids shadowing stdlib `types` when the hooks dir lands on `sys.path`.

**Consumers:**
- `skill-logger.py` — parses `PostToolUsePayload` via `hook_types.parse("PostToolUse", sys.stdin.read())`.
- `safety-gate.py` — parses `PreToolUsePayload`, uses `bash_command()` helper to extract the command string.
- `modes.py` — parses `UserPromptSubmitPayload`.
- `notify.py` — parses multiple payload types depending on the event it's wired into.

### Abstraction 2 — Declarative Hook Registration

**Defines:** `hooks/hooks.json`
**Shape:**
```json
{
  "hooks": {
    "<EventName>": [
      { "matcher": "<optional regex>", "hooks": [ {"type": "command", "command": "<path>", "async": true?} ] }
    ]
  }
}
```
Events wired: `SessionStart` → `session-start`; `UserPromptSubmit` → `modes.py`; `PreToolUse` (matcher `Bash`) → `safety-gate.py`; `PostToolUse` (matcher `.*`) → `skill-logger.py`; `Stop`, `PermissionRequest`, `Notification` → `notify.py` (async).

**What it's FOR:** A single source of truth for what fires when. `${CLAUDE_PLUGIN_ROOT}` is interpolated at install time; the file is merged into `~/.claude/settings.json` by the installer. Matchers scope expensive hooks to the tool types they care about (safety-gate only runs for Bash — the only tool that can execute arbitrary code).

**Consumers:**
- `hooks/install-hooks.sh` — merges this JSON into user settings.
- `hooks/install-gemini-hooks.sh` — the Gemini-CLI variant of the same thing.
- The Claude Code runtime itself — reads settings.json and dispatches to the commands on each event.

### Abstraction 3 — The Hook Script Convention

**Defines:** every executable under `hooks/` (`skill-logger.py`, `safety-gate.py`, `modes.py`, `notify.py`, `session-start`)
**Shape:** shared contract, not enforced by a base class:
1. Shebang — `#!/usr/bin/env -S uv run --script` with inline PEP 723 deps in a `# /// script ... # ///` block.
2. `sys.path.insert(0, str(Path(__file__).parent))` so `import hook_types` resolves (uv-run scripts don't get their own dir on sys.path automatically).
3. Read JSON from stdin, feed to `hook_types.parse(<event>, ...)`.
4. On empty/malformed payload, exit 0 immediately (fail-safe).
5. Perform side effect (log, block, notify, inject).
6. Exit code: 0 = allow/no-op; non-zero from a `PreToolUse` hook = block the tool call.

**What it's FOR:** Uniform, composable, single-responsibility hooks. Adding a new hook is copy-and-edit from an existing script. The fail-safe exit-0 posture means a broken hook doesn't brick Claude Code — payload-read errors silently pass the event through.

**Consumers:**
- The Claude Code runtime invokes them per `hooks.json`.
- `install-hooks.sh` chmods them +x at install time.
- `hooks/tests/` covers payload parsing and edge cases.

### Abstraction 4 — Two-Layer Logging Pipeline

**Defines:** `hooks/skill-logger.py` (owner); consumed by `tools/python/src/af/` modules.
**Shape:** two on-disk logs + per-session state, all JSONL.
- **Layer 1 (session trace):** every tool call → `~/.claude/logs/sessions/session-<id>.jsonl`. Entry shape: `{ts, session, tool, input, output[truncated 1000 chars]}`. Retention: 7 days.
- **Layer 2 (skill invocation log):** Read tool calls whose `file_path` ends in `SKILL.md` → `~/.claude/logs/agentfiles.jsonl`. Entry shape: `{ts, skill, session, parent_skill, escalated, self_loop, chain_depth}`. Category-router skills (directories with child `SKILL.md`) are skipped. Rotation: 5 MB rolling (keep latest half).
- **Per-session state:** `~/.claude/logs/.sessions/<id>.json` = `{last_skill, skills_seen, escalated}`. Retention: 24h. Cleanup throttled by a marker file, roughly every 50 invocations if the marker is >1h old.
- **Escalation detection rule (encoded in skill-logger):** if `manager` is loaded in a session where `executor` already ran, mark escalated.
- **Self-loop detection:** skill == parent_skill.

**What it's FOR:** Capture skill usage and full session traces for introspection, retrospectives, and catching anti-patterns (escalation, self-loops, excessive chain depth). Layer 1 is for debugging a specific session; Layer 2 is for aggregate analysis over time.

**Consumers:**
- `af log` (`tools/python/src/af/log.py`) — reads and filters the logs.
- `af skill-usage` (`skill_usage.py`) — aggregates per-skill counts.
- `af learn` (`learn.py`) — surfaces patterns.
- `af metrics` (`metrics.py`) — aggregate metrics across sessions.

### Abstraction 5 — Policy / Gating Hooks

**Defines:** `hooks/safety-gate.py`, `hooks/modes.py`
**Shape:**
- **safety-gate.py** — PreToolUse hook, scoped to the `Bash` matcher. Reads the command string via `hook_types.bash_command()`. Exits non-zero to veto risky commands; exits 0 to allow. This is the only hook in the set that can *block* a tool call.
- **modes.py** — UserPromptSubmit hook. Reads the active mode(s) from on-disk state (toggled by `af mode on/off`), then re-injects the mode header/instructions into the turn context. Runs on every user prompt.

**What it's FOR:** Policy layer on top of the skill system — safety-gate enforces "what is this agent allowed to do" (blocking is an exit code), modes.py enforces "how should this agent behave this turn" (constant re-injection makes modes durable across compactions).

**Consumers:**
- The Claude Code runtime (consults them on every gated event).
- `af mode` (`tools/python/src/af/mode.py`) — toggles the state modes.py reads.
- `agentfiles/modes/<name>/MODE.md` — the source documents modes.py injects.

## Step 3 — How They Fit Together (Execution Path)

Single tool call, start to end:

1. User prompt arrives → Claude Code fires `UserPromptSubmit` → `modes.py` runs → re-injects mode context if any.
2. Claude decides to run, say, `Bash "rm -rf ..."` → `PreToolUse` with matcher `Bash` → `safety-gate.py` runs → exit 0 allows, exit non-zero blocks.
3. Tool runs → `PostToolUse` matcher `.*` → `skill-logger.py` runs → appends to session log; if the call was `Read SKILL.md`, also appends to the skill log and updates session state.
4. Claude stops → `Stop` → `notify.py` runs async (desktop notification).

## Step 4 — Additional Observations

- **Fail-safe by design.** Every hook exits 0 on malformed input. A broken hook degrades to no-op, never blocks.
- **Async vs sync.** Only `notify.py` is declared `async` in hooks.json. Everything that gates (safety-gate) or logs (skill-logger) is sync.
- **Matcher granularity matters for performance.** safety-gate is narrowed to `Bash`; skill-logger runs on everything because it needs full session trace. If skill-logger's filtering logic moved into the matcher, the CPU cost on non-Read tools would drop.
- **Two installers.** `install-hooks.sh` targets Claude Code; `install-gemini-hooks.sh` targets Gemini CLI. They consume the same `hooks.json` conceptually but install into different targets.

## Step 5 — When to Stop

You can answer:

- **"Where would I add a hook that records every subagent spawn?"** → new script under `hooks/` following the convention; add to `hooks.json` under `PreToolUse` with matcher `Agent`; parse stdin with `hook_types.PreToolUsePayload`; append to a new JSONL.
- **"What would break if I renamed `hook_types.py` to `types.py`?"** → every hook that does `sys.path.insert(0, ...)` then `import hook_types` would fail because `types.py` would shadow the stdlib `types` module, breaking `enum` imports. The comment in the file warns about this explicitly.
- **"What does `safety-gate.py` depend on?"** → hook_types.parse (for payload shape), hook_types.bash_command (for command extraction), the `Bash` matcher in hooks.json (for scoping), and exit code 0/non-zero as the contract with Claude Code.

### Pitfalls to note

- The logging pipeline's two logs have different retention rules (7 days vs 5 MB rolling). Long-running heavy sessions can push the skill log past its rotation even while the session log stays intact. When debugging "where did that skill invocation go," check the right log.
- The escalation rule in skill-logger keys on literal strings `manager` / `executor`. Renaming those skills silently breaks escalation detection.
- `${CLAUDE_PLUGIN_ROOT}` is an install-time substitution; editing `hooks.json` at the repo level and expecting runtime-level re-interpolation will not work.
