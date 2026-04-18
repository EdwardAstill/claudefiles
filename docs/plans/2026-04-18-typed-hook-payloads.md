# Typed Hook Payloads

**Status:** Phase 1 landed (2026-04-18) — shared TypedDict module + safety-gate migration. Phase 2 pending (skill-logger, notify, caveman-mode).
**Inspired by:** `johnlindquist/claude-hooks` — see `research/projects/education-and-showcases/johnlindquist-claude-hooks.md`

## Status

### Phase 1 — DONE (2026-04-18)

- Committed option is **(a) Stay Python + add TypedDicts per event** (not Pydantic; zero runtime deps).
- Shared module: `hooks/hook_types.py` (194 lines, stdlib only).
  - One `TypedDict(total=False)` per event we hook: `SessionStartPayload`, `UserPromptSubmitPayload`, `PreToolUsePayload`, `PostToolUsePayload`, `StopPayload`, `PermissionRequestPayload`, `NotificationPayload`.
  - Common fields factored into `BasePayload` via inheritance.
  - Helpers: `parse(event, raw)` → returns dict matching the event's TypedDict, empty dict on malformed input (never raises); `tool_name(payload)` → handles `tool_name`/`tool`; `bash_command(payload)` → handles `tool_input.command`/`input.command`/top-level `command`.
  - **Why `hook_types.py`, not `types.py`:** putting a `types.py` on `sys.path` shadows the stdlib `types` module and breaks anything that imports `enum` (which pulls `types`). The `hook_` prefix avoids that footgun — discovered during migration, documented in the module docstring.
- Reference migration: `hooks/safety-gate.py` — swaps the manual `.get(...).get(...)` chain for `hook_types.parse("PreToolUse", sys.stdin.read())` + `hook_types.tool_name()` + `hook_types.bash_command()`. All 18/18 `hooks/tests/test_safety_gate.py` cases still pass; behavior unchanged (same block patterns, same exit codes, same fail-safe-exit-0 on malformed input).
- New tests: `tools/python/tests/test_hook_types.py` (14 tests: 7-event round-trip, malformed JSON, non-object JSON, unknown events, flat/nested/legacy shape variants for both helpers). Full pytest suite: 168 passed, 1 skipped.
- `af audit`: 9/9 checks pass, 0 issues. Check 9 (hook script health) ignores `hook_types.py` because it has no shebang and no PEP-723 script block — it's a library, not a hook.

### Phase 2 — TODO

Migrate the remaining three hooks using the same pattern. Recipe:

1. Add after existing `import sys` / `os`:
   ```python
   from pathlib import Path
   sys.path.insert(0, str(Path(__file__).parent))
   import hook_types  # noqa: E402
   ```
2. Replace the `json.load(sys.stdin)` + manual field resolution with:
   ```python
   payload: hook_types.<EventName>Payload = hook_types.parse("<EventName>", sys.stdin.read())
   if not payload:
       sys.exit(0)
   ```
3. Swap `data.get("tool_name") or data.get("tool")` → `hook_types.tool_name(payload)`.
4. Swap the `tool_input.command` chain → `hook_types.bash_command(payload)` (if applicable).
5. Keep all non-payload logic (env-var fallbacks, state files, notify-send calls) untouched.
6. Run the hook's smoke test if it has one; otherwise fire a canned payload with `printf ... | hook.py`.

Specific per-hook notes for Phase 2:

- **`skill-logger.py`** (PostToolUse): keeps its `CLAUDE_SESSION_ID` env-var fallback — that's not a payload shape, it's a cross-process channel. Use `payload.get("session_id")` then fall back to env. `tool_input`/`tool_output` access stays the same shape; `hook_types.PostToolUsePayload` types them as `dict[str, Any]`.
- **`notify.py`** (Stop + PermissionRequest + Notification): branches on `payload.get("hook_event_name")` — cheapest migration since it's already event-aware. Use `hook_types.parse(event, raw)` after reading `hook_event_name` once to pick the right TypedDict type-hint. Or parse as base and let TypedDict narrowing happen per branch.
- **`caveman-mode.py`** / **`modes.py`** (UserPromptSubmit): migration is more cosmetic since these barely touch the payload today. Still worth doing for consistency.

### Phase 3 — OPEN

Shape of `tool_input` per tool. Currently `dict[str, Any]`. Tighten with per-tool TypedDicts (`BashToolInput`, `ReadToolInput`, `WriteToolInput`) when a hook actually branches on tool-specific fields. Don't pre-model — the original design doc (section 8) was explicit about this.

## 1. Goal

Replace `dict.get()`-based payload parsing in `hooks/*.py` with typed, validated Pydantic models per Claude Code event so schema drift fails loudly at the edge of the script, not silently mid-execution.

## 2. Current state

Every hook reads stdin as raw JSON and picks fields defensively.

- `hooks/safety-gate.py:29-36` reads `tool_name` two ways (`tool_name` or `tool`), then tries `tool_input.command`, `input.command`, and top-level `command`. The inline "flat and nested input shapes" comment admits the author isn't sure which shape arrives.
- `hooks/skill-logger.py:121-131` resolves `session_id` from three sources (payload, nested `session.id`, env var) and double-reads `tool_name`/`tool_input`/`tool_output`.

If Anthropic renames `tool_input` → `toolInput`, every hook silently no-ops and we lose logging/gating with no test failure.

## 3. Options considered

**(a) Stay Python, add Pydantic models per event.** One `hooks/_payloads.py` defines `SessionStartPayload`, `PreToolUsePayload`, etc. Each hook calls `parse_stdin(PreToolUsePayload)`. No new runtime; `uv run --script` already powers every hook.

**(b) Port to TypeScript per johnlindquist.** Rewrite hooks as `.ts` via `bun`/`tsx`. Gains IDE autocomplete; costs a hard Node dep on every user's box.

**(c) Hybrid — JSON Schema as source of truth, codegen per language.** Define `schemas/hooks/*.json`, generate Python TypedDicts and TS interfaces. Most flexible, most plumbing.

## 4. Recommended option — (a) Python + Pydantic

- **Single language.** Every hook and every `tools/python/src/af/*` helper is Python. Introducing TS doubles contributor onboarding surface to save ~300 LOC.
- **Install burden.** `bun`/`tsx` is not safe to assume; `uv` already is (agentfiles ships a `tools/python/` uv project).
- **Pydantic is cheap.** Seven events, ~80 lines of models. Validates in microseconds, works fine under `uv run --script` with `dependencies = ["pydantic>=2"]` in the PEP-723 header.
- **johnlindquist's real win is types, not TS.** Pyright on Pydantic/TypedDicts gives equivalent compile-time checking.

Codegen (c) becomes right once we publish hook payloads externally; today it's overkill.

## 5. Payload catalog

From `research/documentation/claude-code/hooks.md`. Common fields (`session_id`, `transcript_path`, `cwd`, `permission_mode`, `hook_event_name`) on shared `BasePayload`. Per-event additions we actually consume:

| Event | Added fields used | Consumer |
|---|---|---|
| `SessionStart` | `source`, `model`, `agent_type?` | `session-start` |
| `UserPromptSubmit` | `prompt` | `caveman-mode.py` (future use) |
| `PreToolUse` | `tool_name`, `tool_input`, `tool_use_id` | `safety-gate.py` — needs Bash `tool_input.command` |
| `PostToolUse` | `tool_name`, `tool_input`, `tool_response`, `tool_use_id` | `skill-logger.py` — `tool_input.file_path` for Read |
| `Stop` | common only | `notify.py` — `session_id`, `cwd` |
| `PermissionRequest` | `tool_name`, `tool_input`, `permission_suggestions?` | `notify.py` — `tool_name` |
| `Notification` | `message`, `title?`, `notification_type` | `notify.py` — branches on `idle_prompt` |

`tool_input` is a discriminated union on `tool_name`. Model Bash and Read strictly; others fall through to `dict[str, Any]` until a hook cares.

## 6. Migration plan

1. Add `hooks/_payloads.py` — `BasePayload` + one model per event. Strict Bash/Read `tool_input` variants; rest `dict`.
2. Add `parse_stdin(model_cls)` helper: validates, returns model, or exits 0 with `[payload]` stderr warning on `ValidationError`. Exit-0 preserves current fail-safe behaviour.
3. Migrate `safety-gate.py` first (smallest). Drop the nested/flat fallback.
4. Migrate `skill-logger.py`. Env-var session-id fallback stays; payload fields become `payload.tool_name` etc.
5. Migrate `notify.py` — branch on `payload.hook_event_name` discriminator.
6. Migrate `caveman-mode.py` for consistency (currently ignores payload).
7. Add `tools/python/tests/test_hook_payloads.py` with real-payload fixtures.

## 7. Testing strategy

- **Fixture corpus.** Harvest one real payload per event from `~/.claude/logs/sessions/`. Commit redacted copies to `tools/python/tests/fixtures/hook_payloads/`.
- **Round-trip.** `test_payload_parses_real_samples` loads each fixture, asserts no `ValidationError`.
- **Drift guard.** Models use `model_config = ConfigDict(extra="allow")` — new upstream fields never break us; we only fail on *missing required* fields.
- **Live smoke.** `af hooks smoketest` (new subcommand) pipes canned JSON into each script and asserts exit code 0.

## 8. Risks / open questions

- **Pydantic install latency.** First `uv run --script` on a fresh box resolves Pydantic (~2s). Acceptable; note in release.
- **Schema drift.** Mitigated by `extra="allow"` plus dated header in `_payloads.py` citing the fetch date of the canonical hooks doc. Re-fetch quarterly.
- **Open:** shared model module vs inline per-hook? Proposal: shared, for honest drift detection.
- **Open:** `tool_input` union covers Bash + Read today. Extend when a hook cares about Edit/Write — don't pre-model.
- **Open:** TS wins if agentfiles ever ships hooks as a marketplace (johnlindquist's "Hook Marketplace" note). Re-evaluate only if that lands.
