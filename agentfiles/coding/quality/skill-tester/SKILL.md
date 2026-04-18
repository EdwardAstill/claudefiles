---
name: skill-tester
description: >
  Tests and evaluates agentfiles skills by running them against hard benchmark
  questions and grading outputs on a rubric. Use when you want to measure
  whether a skill adds value, after running `af test-skill <name>`, or when
  asked to test, evaluate, benchmark, or grade a skill. Triggers on: "test
  this skill", "does this skill help", "evaluate the skill", "benchmark",
  "run evals", "grade the skill", or any request to measure skill quality.
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
