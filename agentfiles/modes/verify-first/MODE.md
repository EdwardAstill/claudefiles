---
name: verify-first
description: >
  Run test/typecheck/smoke-check and quote the output before claiming a
  change "works." Kills hallucinated green lights — if the agent didn't
  see a passing run, it doesn't claim one.
category: rigor
levels: [on]
reminder: >
  verify-first: before claiming a change works, run the relevant test,
  typecheck, or smoke check and quote the actual output. No
  "should work" / "this will pass" language — run it. If the tool is
  missing or the run fails, say so; do not fabricate a passing result.
conflicts_with: []
auto_clarity: false
---

# verify-first

The "prove it" mode. Stops the agent from writing "this should work" and
forces an actual run with quoted output before any success claim.

## When to use

- Code changes that touch logic, types, or tested behavior.
- Bug fixes — the fix isn't done until the reproducer is green.
- Any task where the user cares whether the thing actually runs.

## Rules

- **Run before claiming.** Tests, typecheck, linter, or smoke check —
  whichever matches the change. Don't claim success without a run.
- **Quote the output.** A short excerpt (pass count, error line) proves
  you saw it. "All tests pass" without output is not verification.
- **No hedge words as a shortcut.** "Should work," "will pass,"
  "probably fine" — banned as substitutes for running the check.
- **Report failure honestly.** If the run fails or the tool is missing,
  say so. Do not fabricate a green result.
- **Scope the check.** Run the targeted test/module, not the whole
  suite, unless the change is cross-cutting.

## Escape hatches

- Pure documentation or comment changes — no runnable behavior to verify.
- Config edits with no validator — note what would verify it in
  production.
- Long-running suites — run the nearest targeted check and say which
  broader check is recommended before merge.

## Persistence

State file: `~/.claude/modes/verify-first`. The `UserPromptSubmit` hook
re-injects the reminder each turn. Control:

```bash
af mode on verify-first
af mode off verify-first
af mode status
```

## Interaction with other modes

- Pairs well with `caveman-full` (terse AND proof-backed — the original
  motivating combo).
- Stacks with `deep-research` for research-then-verify flows.
- Does not conflict with any existing mode.
