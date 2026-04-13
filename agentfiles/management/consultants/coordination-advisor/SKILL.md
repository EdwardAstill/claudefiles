---
name: coordination-advisor
description: >
  Use when manager needs to decide how to structure agent teams: which tasks run in
  parallel vs sequentially, what dependencies exist, how to split complex work across
  multiple agents. Single mandate: answer "how should agents be coordinated for this
  plan?" Loaded inline by manager during planning — never dispatched as a subagent.
---

# Coordination Advisor

Your only job: determine the optimal agent coordination structure for this plan —
parallel vs sequential, team composition, dependencies, and dispatch pattern.

---

## Parallel vs sequential

**Run in parallel when:**
- Tasks have no shared state (won't edit the same files)
- No task depends on another's output
- Parallelism saves meaningful time — tasks are non-trivial

**Run sequentially when:**
- Task B needs Task A's output
- Tasks share mutable state (same files, same database, same config)
- Parallelism adds coordination complexity without saving time

**Mixed:** Some tasks can run in parallel within a sequential pipeline — identify the
dependency graph and maximise concurrency at each stage.

## Team structures

**One agent per independent domain** — the default. Each agent gets:
- A specific scope (one feature, one subsystem, one file group)
- A clear goal and expected output format
- A constraint on what not to touch

**Lead + supporting agents** — for tasks where one agent makes architectural decisions
that others implement. Lead runs first, produces a design or interface spec, then
supporting agents implement against it in parallel.

**Pipeline** — Agent A → Agent B → Agent C, each building on the previous output.
Use when work is inherently sequential but each stage is large enough to warrant
fresh context.

## Dispatch patterns

| Pattern | Use when |
|---------|----------|
| Parallel Agent calls (single message, multiple Agent tool calls) | Independent tasks, no ordering constraints |
| `subagent-driven-development` | Sequential tasks where each needs fresh context + review gate |
| Inline (manager executes directly) | Small enough to hold in one context |

## What makes a good agent boundary

- Agent can be given a self-contained prompt with no session history
- Agent's output is a clearly defined artifact (file, report, diff, answer)
- Agent's scope doesn't require knowledge of what other agents are doing
- If an agent needs to know what another is doing — they should be sequential, not parallel

---

## How to respond

Map out the dependency graph first. Then give a concrete coordination plan: which
agents run when, what each produces, how outputs connect. Name the dispatch pattern.
Flag any shared state risks you see in the plan.
