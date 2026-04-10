---
name: cheapskill
description: >
  Token-minimal execution path for simple tasks. Invoked by task-analyser when all
  complexity signals are Simple: 1-2 subtasks, single domain, no coordination needed.
  Uses the cheapest/fastest available model (haiku or equivalent). No planning overhead,
  no review steps, no subagents. Direct execution only.
---

# Cheapskill

Fast, token-minimal execution for simple, well-defined tasks.

**Model:** Use the cheapest/fastest available model (haiku or equivalent).

## Behaviour

Receives from task-analyser:
- Task text
- Subtask list (1–2 items)

Execute directly:
1. Work through each subtask in sequence
2. No planning phase
3. No review steps
4. No subagents

Return the result.

## Constraints

- Do not invoke other skills
- Do not dispatch subagents
- Do not ask the user for confirmation unless the task is genuinely ambiguous
- If the task turns out to be more complex than routed, report back — do not expand scope
