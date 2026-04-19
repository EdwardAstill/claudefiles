---
name: planner
description: >
  Numbered plan before tool calls. Forces the agent to surface its
  intended sequence of steps, and to pause for user approval when the
  plan exceeds a small-step threshold.
category: planning
levels: [on]
reminder: >
  planner: before running any tool, emit a short numbered plan of the
  steps you intend to take. If the plan has more than 5 steps or
  touches files outside the current task scope, stop after the plan
  and wait for user approval before executing. Keep steps concrete
  (file paths, commands), not abstract.
conflicts_with: []
auto_clarity: false
---

# planner

The "show your work before you do it" mode. Turns the agent's implicit
plan into an explicit, user-reviewable plan — cheap insurance against
scope creep and wrong-direction execution.

## When to use

- Multi-step tasks where a wrong first step wastes the rest.
- Tasks touching several files or modules — the plan makes the blast
  radius visible.
- Situations where the user wants to stay in the loop on sequencing.

## Rules

- **Plan first.** Before any non-readonly tool call, emit a numbered
  list of the steps you intend.
- **Concrete steps.** "Edit `src/foo.py` to rename `bar` → `baz`" beats
  "update the foo module." File paths and commands, not vibes.
- **Pause threshold: 5 steps.** Plans of ≤5 steps can execute
  immediately. Plans of >5 steps, or plans touching files outside the
  stated scope, stop and wait for approval.
- **Revise out loud.** If execution surfaces a reason to deviate from
  the plan, call that out, amend the plan, and continue.
- **Read-only tools are free.** Exploration (Read, Grep, Glob) doesn't
  need a plan — those are how you build one.

## Anti-patterns

- Vague plans ("1. understand the code 2. make changes"). If that's
  all you can say, you haven't planned.
- Skipping the plan because "it's only a few steps" — write the few
  steps.
- Executing past the approval threshold without waiting.

## Escape hatches

- Single-step trivial tasks (one read, one reply). Plan is overkill.
- Tasks explicitly marked "just do it" or "no plan needed" by the user.

## Persistence

State file: `~/.claude/modes/planner`. The `UserPromptSubmit` hook
re-injects the reminder each turn. Control:

```bash
af mode on planner
af mode off planner
af mode status
```

## Interaction with other modes

- Pairs with `rubber-duck` — duck clarifies the intent, planner
  sequences the execution.
- Pairs with `verify-first` — plan the steps, run the checks.
- Compatible with communication modes (`caveman`, `token-efficient`) —
  the plan format is already terse.
- Does not conflict with any existing mode.
