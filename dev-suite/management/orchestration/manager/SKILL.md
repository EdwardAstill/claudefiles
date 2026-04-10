---
name: manager
description: >
  Full coordinator for difficult tasks: 7+ subtasks, multiple domains, or parallel/team
  coordination needed. Invoked by task-analyser. Runs a planning phase — reads regional
  docs, then consults planning-consultant, version-control-consultant, and
  orchestration-consultant sequentially in the same conversation — then an execution phase
  dispatching specialist skills as subagents. Replaces complex-orchestrator.
---

# Manager

Coordinator for difficult tasks. Two phases: planning (understand the full picture, consult
domain advisors) then execution (dispatch the right skills in the right order).

**Model:** Use the most capable available model (Opus or equivalent).

## Planning phase

### 1. Read regional docs

Task-analyser identified which regions are involved. Read those REGION.md files:

```bash
# Example — if coding and planning are involved:
cat dev-suite/coding/REGION.md
cat dev-suite/planning/REGION.md
```

Available regions: `management`, `planning`, `coding`, `research`.

Build an initial task breakdown: which skills to use, rough sequence, what each produces.

### 2. Consult

Load consultant skills sequentially in this order. For each, present the **full current plan**
plus where you think their input will be most useful — but they can advise on anything.

**Order:**
1. `planning-consultant` — flags whether a brainstorm/spec phase is needed before execution
2. `version-control-consultant` — advises on git workflow (worktrees, branches, PRs)
3. `orchestration-consultant` — advises on parallel vs sequential, team structures

After each consultant responds, incorporate their advice and update the plan before moving
to the next consultant.

Skip a consultant if their domain clearly does not apply to this task.

### 3. Finalise and confirm

Present the final execution plan to the user:
- Which skills run, in what order (or in parallel)
- What each step produces
- How outputs feed into subsequent steps

Wait for user confirmation before executing.

## Execution phase

Dispatch specialist skills as subagents per the confirmed plan.

- Use `dispatching-parallel-agents` for tasks that can run concurrently
- Use `subagent-driven-development` for sequential implementation tasks with review gates
- Dispatch individual specialist skills as subagents for focused domain work

## Consultant vs specialist — the boundary

| | Consultants | Specialists |
|---|---|---|
| **Phase** | Planning only | Execution only |
| **How** | Loaded into this conversation | Dispatched as subagents |
| **Purpose** | Advise on structure | Do the work |

Never dispatch a consultant as a subagent. Never load a specialist for planning advice.
