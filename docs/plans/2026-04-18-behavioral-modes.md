# Behavioral Modes — Implementation Plan

**Status:** MVP shipped (2026-04-18) — primitive, CLI, hook, and two modes (token-efficient + caveman) live.
**Inspired by:** `SuperClaude_Framework` — see `research/projects/skill-suites/superclaude-framework.md`

## Status

### Done (MVP)

- `agentfiles/modes/` primitive with authoring guide (`modes/README.md`).
- Two modes shipped: `agentfiles/modes/token-efficient/MODE.md` and `agentfiles/modes/caveman/MODE.md` (ported from the old communication/caveman SKILL.md).
- Generic `hooks/modes.py` (multi-mode dispatcher) — reads `~/.claude/modes/`, concatenates reminders in category order, emits one `UserPromptSubmit` payload. Zero external deps, inline YAML-ish parser for the frontmatter subset we commit to.
- State layout: directory `~/.claude/modes/`, one file per active mode (contents = level). Overridable via `$AF_MODES_STATE_DIR` for tests.
- CLI `af mode list|on|off|status` with `--active`, `--level`, conflict detection, and clean errors on unknown mode/level. Registered in `tools/python/src/af/main.py`.
- `af caveman` kept as backwards-compat alias (writes to the new state dir; migrates the legacy `~/.claude/caveman-mode` file on first use).
- `hooks/hooks.json` swapped `caveman-mode.py` → `modes.py`. Old `caveman-mode.py` kept as a one-release shim that delegates to `modes.py`.
- Tests: `tools/python/tests/test_mode.py` — 13 tests (discovery, parse, activate/deactivate, CLI list/on/off/status, unknown-mode, unknown-level, priority ordering, caveman alias, hook subprocess integration).
- `af audit` stays 8/8. Full test suite 141 passed / 1 skipped.

### Remaining (later passes)

- Ship `deep-research`, `verify-first`, `rubber-duck`, `planner` modes (one MODE.md each — primitive already supports them).
- `af check` validator for MODE.md frontmatter (required keys, known category, conflicts_with resolves, unique names, no SKILL.md under modes/, no MODE.md outside it).
- Delete `agentfiles/communication/caveman/SKILL.md` and its `[skills.caveman]` manifest entry once callers (marketplace blurb, hooks/install-*.sh, docs/skill-tree.md, tools/python/tests/test_cli_smoke.py) are migrated.
- Delete `hooks/caveman-mode.py` shim next release.
- Per-project modes (`af mode on --project` → `.claude/modes/` in the repo) — open question from section 9.
- Named bundles (`af mode preset research-deepdive`) — deferred per section 9.
- Raise conflict-line bloat cap (currently none; plan calls for 5-active limit).

### On-the-fly design calls

- **YAML parsing:** no PyYAML dep. Inline minimal parser covers folded scalars (`>`), inline lists (`[a, b]`), dash-lists, and one-level mappings (for `reminders:` and `aliases:`). Same parser lives in `mode.py` and `hooks/modes.py`; duplication is intentional to keep the hook deps-free.
- **State override envs:** `$AF_MODES_STATE_DIR` + `$AF_MODES_DIR` for tests. Production code never sets them.
- **Caveman shim order:** callback runs `_migrate_legacy()` every time before dispatching, so muscle-memory invocations are silently migrated on first run.
- **Audit vs port:** kept `agentfiles/communication/caveman/SKILL.md` in place (and its `[skills.caveman]` manifest entry) to avoid a cross-cutting cleanup pass. Listed above as a remaining follow-up.

## 1. Goal

Introduce `agentfiles/modes/<name>/MODE.md` as a first-class primitive for cross-cutting operating postures (token-efficient, deep-research, verify-first, rubber-duck, caveman), activated via `af mode on/off/list` and re-injected by one generic `UserPromptSubmit` hook — so future modes ship in one file instead of re-cloning the caveman pattern.

## 2. What's a mode (vs a skill)?

A **skill** is a procedure-for-task: "when asked to write Python, apply `python-expert`." Task-triggered, scoped to one job.

A **mode** is a cross-cutting posture: "for the rest of this session, minimise output length." User-triggered, session-scoped, orthogonal to which skill runs, affects *how* every skill renders output / chooses depth / verifies itself.

Test: instruction describes *what to do* → skill. Describes *how to behave across everything* → mode. `caveman` flunks the skill test — not "when X, grunt," but "for every reply, be terse."

## 3. Current state

`caveman` is the only mode, implemented ad-hoc in four pieces:

- `agentfiles/communication/caveman/SKILL.md` — human-facing doc (filed under `communication/` because there was no `modes/`).
- `hooks/caveman-mode.py` — `UserPromptSubmit` hook. Reads `~/.claude/caveman-mode` each turn, emits `additionalContext` with a per-level reminder.
- `tools/python/src/af/caveman.py` — `af caveman on/off/status`, writes the state file.
- `hooks/hooks.json` — statically registers the hook.

Mechanism: state file → per-turn hook → `additionalContext` → mode persists across sessions because the file does. New modes must clone all four pieces.

## 4. Proposed primitive

```
agentfiles/modes/
  caveman/MODE.md
  token-efficient/MODE.md
  deep-research/MODE.md
  verify-first/MODE.md
  rubber-duck/MODE.md
```

**Frontmatter schema:**

```yaml
---
name: deep-research
description: >
  Wide parallel fanout, 3+ sources cited, no memory-only answers.
category: research        # communication | research | rigor | planning | novelty
reminder: >
  deep-research: fan out across 3+ sources in parallel, cite each, prefer
  primary docs (context7) over web search, do not answer from memory alone.
levels: [on]              # optional; caveman keeps [lite, full, actual-caveman]
conflicts_with: [token-efficient]   # optional
auto_clarity: false       # optional; true = drop posture for safety-critical blocks
---
```

Body = human doc (examples, when-to-use, escape hatches). `reminder:` is what the hook injects.

**Candidates beyond caveman:**

- **token-efficient** — cap replies at N lines, code-and-command only, keep grammar (softer than caveman-full).
- **deep-research** — force multi-source fanout, require citations, no memory-only answers.
- **verify-first** — run test/typecheck/smoke check and quote output before claiming "works." Kills hallucinated green lights.
- **rubber-duck** — ask one clarifying question before editing; wait for reply.
- **planner** — numbered plan before tool calls; approval required on plans > N steps.

## 5. Activation / deactivation

CLI: `af mode on <name> [level]`, `af mode off <name>`, `af mode list`, `af mode status`.

**Multiple stackable.** Reasoning: `caveman-full` + `verify-first` is a coherent combo (terse *and* proof-backed). Single-active would force a choice between orthogonal axes. Cost of stacking is one reminder line per active mode — cheap.

State = directory `~/.claude/modes/`, one file per active mode (contents = level, default `on`). Replaces `~/.claude/caveman-mode`.

## 6. Persistence

Survives session boundaries via the state directory — same mechanism caveman uses today, generalised.

Rewrite `hooks/caveman-mode.py` as `hooks/modes.py`: scan `~/.claude/modes/`, read each active mode's `reminder:`, concatenate, emit one `additionalContext` payload per turn. One hook covers all modes — no new hook registration per mode.

## 7. Conflict resolution

1. **Declared conflicts** — `conflicts_with:` in frontmatter. `af mode on` refuses, names the conflict, suggests `af mode off <other>`.
2. **Auto-clarity override** — modes with `auto_clarity: true` yield to safety-critical blocks (destructive warnings, multi-step instructions, security notes). Mirrors caveman's current rule.
3. **Reminder order = priority.** Emit order: `rigor` (verify-first, planner) → `research` → `communication` (caveman, token-efficient) → `novelty`. On same-category contradiction, last wins (recency). Document in `agentfiles/modes/README.md`; revisit on real conflict.

## 8. Migration

1. Create `agentfiles/modes/` + `modes/README.md` (priority order, catalogue).
2. Add `tools/python/src/af/mode.py` (`on/off/list/status`); register in `main.py`.
3. Add `hooks/modes.py`. Leave `caveman-mode.py` as a one-release shim, then delete.
4. Port `communication/caveman/SKILL.md` → `modes/caveman/MODE.md`. Levels → `levels:` list; per-level strings → `reminders:` map.
5. Keep `af caveman <level>` as alias for `af mode on caveman <level>`.
6. Update `hooks/hooks.json`: swap `caveman-mode.py` for `modes.py`.
7. Ship `token-efficient`, `verify-first`, `deep-research` one PR each.
8. `af check` validates MODE.md frontmatter (required keys, known category, unique names, `conflicts_with:` resolves).

## 9. Risks / open questions

- **Reminder bloat.** Cap at 5 active modes; `af mode on` refuses the 6th.
- **Skill vs mode drift.** Contributors will file modes as skills (caveman did). `af check` warns on `SKILL.md` under `modes/` or `MODE.md` outside it.
- **Per-project modes.** Some modes (e.g. `verify-first`) are repo-specific. Open: `af mode on --project` writes to `.claude/modes/` in the repo. Defer.
- **Level schema.** Most modes want one level. `levels:` defaults to `[on]` to keep the common case one line.
- **Open:** `af mode list` active-only, `--all` for catalogue (git-branch style)? Propose yes.
- **Open:** named bundles (`af mode preset research-deepdive`)? Defer until 2+ users ask.
