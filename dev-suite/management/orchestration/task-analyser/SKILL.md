---
name: task-analyser
description: >
  Always-on entry point. Activates at the start of every task before any other skill acts.
  Decomposes the task into subtasks, scores complexity across scope/domain/coordination,
  then routes to cheapskill (simple: 1-2 subtasks, single domain, no coordination),
  superskill (medium: 3-6 subtasks, manageable solo), or manager (difficult: 7+ subtasks,
  multiple domains, or parallel/team coordination needed). Use at the start of every task.
---

# Task Analyser

Always-on triage layer. Decomposes every incoming task, assesses complexity, and routes to
the right execution path. Nothing else runs until task-analyser has decided where to send it.

## Step 1: Decompose

Break the task into concrete subtasks. Be specific — each subtask should be a discrete unit
of work with a clear output.

## Step 2: Score complexity

Score across three signals:

| Signal | Simple | Medium | Difficult |
|--------|--------|--------|-----------|
| Subtask count | 1–2 | 3–6 | 7+ |
| Domain spread | Single | Single, some unknowns | Multiple domains |
| Coordination needed | None | None | Parallel / team |

Any signal hitting **Difficult** → manager.
All signals **Simple** → cheapskill.
Otherwise → superskill.

**When in doubt, route to the more capable path.** Routing to superskill instead of cheapskill
costs a few extra tokens. Routing to cheapskill when manager was needed wastes the whole task.

## Step 3: Gather codebase context

```bash
cf-context   # project fingerprint: name, language, structure
cf-status    # git state: branch, recent commits, uncommitted changes
```

If neither tool is available, skip this step.

## Step 4: Route with context

Announce the routing decision:

```
Routing to [cheapskill | superskill | manager]
Reason: [which signal(s) triggered this, subtask count: N]
Subtasks:
  1. [subtask]
  2. [subtask]
  ...
```

Then invoke the target skill with:
- **cheapskill:** task text + subtask list
- **superskill:** task text + subtasks + cf-context/cf-status output
- **manager:** task text + subtasks + which regions are involved + cf-context/cf-status output
