# Typed Hook Payloads

**Status:** proposed
**Inspired by:** `johnlindquist/claude-hooks` — see `research/projects/education-and-showcases/johnlindquist-claude-hooks.md`

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
