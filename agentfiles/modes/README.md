---
name: modes-catalogue
description: >
  Behavioral modes — cross-cutting postures activated with `af mode on/off`,
  re-injected each turn by `hooks/modes.py`.
---

# Behavioral Modes

A **mode** is a cross-cutting operating posture (terse, deep-research,
verify-first, etc.) that affects *how* every skill renders output. Unlike a
skill, a mode is user-triggered and session-scoped, orthogonal to the task.

State lives in `~/.claude/modes/` — one file per active mode, filename is
the mode name, contents are the active level (default `on`). The
`UserPromptSubmit` hook (`hooks/modes.py`) scans this directory each turn,
reads each mode's `reminder:` from its MODE.md, and injects one
`additionalContext` payload containing the concatenated reminders.

## Modes in this repo

- `token-efficient` — cap replies short; code-and-command only; keep grammar.
- `caveman` — terse communication with three levels (lite / full /
  actual-caveman); original ad-hoc mode, ported to this primitive.

## CLI

```
af mode list                 # catalogue + active state
af mode list --active        # active-only
af mode on <name> [--level lvl]
af mode off <name>
af mode status               # active modes only
```

## Authoring a mode

Create `agentfiles/modes/<name>/MODE.md` with this frontmatter:

```yaml
---
name: <name>
description: >
  One-paragraph human summary.
category: communication       # communication | research | rigor | planning | novelty
reminder: >
  Short sentence the hook will inject each turn.
levels: [on]                  # optional; default [on]. Multi-level modes list them here.
reminders:                    # optional; only needed if `levels` has more than one entry.
  lite:  "…"
  full:  "…"
conflicts_with: [other-mode]  # optional
auto_clarity: false           # optional; true = yield to safety-critical blocks
---
```

The body is human documentation (examples, when-to-use, escape hatches).
Only frontmatter is consumed by the runtime.

## Priority order (when multiple active)

Reminders are concatenated in category order:

1. `rigor` (verify-first, planner)
2. `research` (deep-research)
3. `communication` (caveman, token-efficient)
4. `novelty`

Within a category, last-activated wins on a same-category contradiction.

## Conflicts

`conflicts_with:` in frontmatter is enforced by `af mode on`. Trying to
activate a mode that conflicts with an already-active one fails and names
the conflict; deactivate the other first.
