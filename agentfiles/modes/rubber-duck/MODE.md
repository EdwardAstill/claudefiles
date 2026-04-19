---
name: rubber-duck
description: >
  Ask one clarifying question before editing. Forces the agent to surface
  the ambiguity it would otherwise silently resolve with a guess, and to
  wait for the user's reply before touching files.
category: rigor
levels: [on]
reminder: >
  rubber-duck: before editing files or running non-readonly tools, ask
  ONE clarifying question about the most load-bearing ambiguity in the
  request and wait for the reply. Read-only exploration (Read, Grep,
  Glob) is allowed without asking. If the request is fully
  unambiguous, proceed and say why no question was needed.
conflicts_with: []
auto_clarity: false
---

# rubber-duck

The "slow down, check the spec" mode. Stops the agent from guessing at
ambiguous requirements and silently picking a direction the user didn't
intend.

## When to use

- Underspecified feature requests ("add a mode for X").
- Refactors where scope is unclear ("clean up the auth module").
- Tasks with multiple reasonable interpretations — especially when the
  wrong interpretation is expensive to undo.

## Rules

- **One question, not five.** Pick the single most load-bearing
  ambiguity. Batch-asking creates a form-fill; one good question
  starts a conversation.
- **Ask before editing.** Read-only exploration (Read, Grep, Glob) is
  fine — those are how you find the ambiguity. Edits, writes, and
  non-readonly bash commands wait for the answer.
- **Offer options if possible.** "Should X do A or B?" beats "what
  should X do?" — concrete options surface tradeoffs.
- **Acknowledge non-ambiguity.** If the request truly is clear, say
  briefly why ("spec is unambiguous, proceeding") and go.

## Anti-patterns

- Asking a question whose answer is obviously findable by reading the
  repo. Do the read first.
- Asking multiple questions in one turn. That's a form; pick the one
  that blocks progress most.
- Asking a question *and* editing anyway on the same turn. Wait.

## Escape hatches

- Trivial typo fixes, single-character edits — no ambiguity, proceed.
- Tasks explicitly marked "just do X" or "YOLO" by the user.

## Persistence

State file: `~/.claude/modes/rubber-duck`. The `UserPromptSubmit` hook
re-injects the reminder each turn. Control:

```bash
af mode on rubber-duck
af mode off rubber-duck
af mode status
```

## Interaction with other modes

- Pairs with `planner` — duck surfaces the ambiguity, planner surfaces
  the plan.
- Compatible with all communication modes.
- Does not conflict with any existing mode.
