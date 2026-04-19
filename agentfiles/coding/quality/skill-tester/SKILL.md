---
name: skill-tester
description: >
  Use when measuring whether an agentfiles skill actually adds value —
  running it against hard benchmark questions and grading outputs on a
  rubric. Trigger phrases: "test this skill", "does this skill help",
  "evaluate the X skill", "benchmark the skill", "run the evals for
  X", "grade the skill against the rubric", "did my changes improve
  the skill", "run af test-skill <name>", "iterate on the skill until
  it passes", "compare skill vs baseline". Dispatches a subagent (see
  agentfiles/agents/skill-tester.md) that runs parallel eval +
  grading, returns a verdict + rubric delta, and writes
  docs/testing/<skill>.md. Do NOT use for authoring a new skill
  (write the SKILL.md directly), for general code review (use
  code-review), or for unit-testing project code (use tdd).
---

# Skill Tester (dispatcher)

This capability now runs as a **subagent** — see
`agentfiles/agents/skill-tester.md`. It's a subagent because it dispatches
many parallel eval and grading runs, and its output is verbose rubric data
the parent doesn't need in context.

## How to invoke

Dispatch via the Agent tool:

```
subagent_type: skill-tester
prompt: |
  Evaluate the <skill-name> skill.
  - Skill path: agentfiles/<category>/<skill-name>/SKILL.md
  - Workspace: tests/<skill-name>/iteration-<N>/
  - Evals: tests/<skill-name>/evals.json (generate if missing)
  Return: rubric delta, token-efficiency delta, verdict, report path.
```

The subagent returns a short summary. Full report lands at
`docs/testing/<skill-name>.md`.

## When to use this skill instead of the subagent directly

Almost never. The skill exists only so that a `/skill-tester` invocation
(or a match on the description triggers) routes to the subagent. If you
already know you want to evaluate a skill, call the Agent tool directly
with `subagent_type: skill-tester`.
