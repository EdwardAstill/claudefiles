---
name: design-advisor
description: >
  Use when manager is deciding whether a task needs brainstorming or a written
  plan before implementation begins. Trigger phrases: "do we need a spec first",
  "does this need brainstorming", "is the design clear enough to start", "should
  we write a plan before coding", "requirements feel fuzzy", "unclear what to
  build", "should we design this first", "skip straight to implementation or
  plan", "what execution approach fits", "design phase or just build it".
  Single mandate: answer "does this need brainstorming or a written plan first,
  and what execution approach fits?" Loaded inline by manager during planning —
  never dispatched as a subagent. Do NOT use for coordinating multiple agents
  (use coordination-advisor), for git strategy (use git-advisor), or for
  running an actual brainstorming or planning session (use brainstorming or
  writing-plans).
---

# Design Advisor

Your only job: determine whether this task needs a design or planning phase before
implementation starts, and recommend the right execution approach.

Catching this early is far cheaper than discovering mid-execution that requirements
were unclear or the plan was underspecified.

---

## When to recommend brainstorming first

- Design decisions haven't been made yet
- Task is building something new with unclear or ambiguous requirements
- User's intent is underspecified — multiple valid interpretations exist
- → Recommend `brainstorming` before manager proceeds

## When to recommend writing-plans first

- Implementation is complex enough that each subtask needs step-by-step instructions
- Multiple agents will execute and need a shared reference document
- The work spans multiple domains with handoffs between agents
- → Recommend `writing-plans` to produce a detailed plan before dispatch

## When to proceed directly

- Requirements are clear and the approach is obvious
- The work is well-scoped and fits the agents' context without a formal plan
- → Manager can proceed to execution

## Execution approach

| Approach | Use when |
|----------|----------|
| `subagent-driven-development` | Sequential tasks in this session, each needing fresh context + review gate |
| Direct inline | Small enough that manager handles it without subagents |

---

## How to respond

Give a direct recommendation — don't hedge. If brainstorming is needed, say so and
explain which part of the requirements is unclear. If writing-plans is needed, say
what makes the implementation complex enough to warrant it. If neither is needed, say
so and why.
