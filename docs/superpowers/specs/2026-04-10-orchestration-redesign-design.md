# Orchestration Redesign — Design Spec

**Date:** 2026-04-10
**Status:** Approved for implementation

---

## Goal

Replace the two-orchestrator system (`simple-orchestrator` + `complex-orchestrator`) with a
5-component architecture that routes tasks by complexity, introduces a capable general agent
for medium tasks, and gives the manager a structured planning phase with domain-aware consultants.

---

## Problem with Current System

- `simple-orchestrator` routes to specialists but has no concept of "do it yourself" — every
  task that isn't trivial escalates to complex-orchestrator
- `complex-orchestrator` reads the full `registry.md` and must carry all domain knowledge
  itself — expensive and brittle
- No cheap/fast path for simple tasks
- No capable general agent for medium tasks that don't need full orchestration
- No structured way to get workflow advice during planning

---

## Architecture

```
task-analyser  →  cheapskill   (simple — haiku, direct execution)
               →  superskill   (medium — Sonnet, general agent)
               →  manager      (difficult — Opus, planning + execution)
                                  ↓
                        reads regional docs
                        consults consultant skills
                        dispatches specialist skills as subagents
```

---

## Components

### task-analyser

Always-on entry point. Replaces both `simple-orchestrator` and `complex-orchestrator` as the
first thing that runs on every task.

**Responsibilities:**
- Decompose the task into subtasks
- Score complexity across three signals:

| Signal | Simple | Medium | Difficult |
|--------|--------|--------|-----------|
| Subtask count | 1–2 | 3–6 | 7+ |
| Domain spread | Single | Single, some unknowns | Multiple domains |
| Coordination needed | None | None | Parallel / team |

Any signal hitting Difficult → manager. All signals Simple → cheapskill. Otherwise → superskill.

**Handoff context:**
- cheapskill: task text + subtask list
- superskill: task text + subtasks + relevant codebase context
- manager: task text + subtasks + which regions are involved + codebase context

---

### cheapskill

**Model:** haiku (or equivalent cheap/fast model)

**Purpose:** Token-minimal execution for simple, well-defined tasks.

**Behaviour:**
- Receives task + subtask list from task-analyser
- Executes directly — no planning overhead, no review steps, no subagents
- Returns result

---

### superskill

**Model:** Sonnet

**Purpose:** Capable general agent for medium-complexity tasks.

**Behaviour:**
- Receives task + subtasks + codebase context
- Breaks subtasks down further as needed
- Has full tool access
- Tests its own solution
- Asks the user for input when genuinely stuck or at a decision point
- Absorbs specialist skills — does not invoke `git-expert`, `python-expert` etc. as subagents;
  handles domain work inline

---

### manager

**Model:** Opus

**Purpose:** Coordinator for difficult tasks requiring multi-agent execution, parallel work,
or cross-domain planning.

**Two phases:**

#### Planning phase

1. Reads the regional docs for whichever domains task-analyser identified as involved
2. Builds an initial breakdown of the full task
3. For each relevant consultant skill:
   - Loads the consultant into the same conversation (not as a subagent)
   - Sends: **full plan** + "I think you can most help with [X, Y, Z] — but review everything"
   - Consultant responds on flagged points and anything else it spots
   - Back and forth until advice is incorporated
4. Synthesises all consultant input into a final execution plan

Consultants are loaded sequentially. Each sees the full evolving plan, not just their slice.
The manager's flagging is a suggestion, not a restriction — consultants can advise on any part.

#### Execution phase

Dispatches specialist skills as subagents per the refined plan. Decides what runs in parallel,
what runs sequentially, and whether any subtasks need a team of agents.

---

### Consultant skills

Live in `dev-suite/management/consultants/`. Each is a small, focused SKILL.md.

Consultants have:
1. **Domain knowledge** for their specialty
2. **Awareness of the relevant skills in the suite** that relate to their domain
3. **Workflow patterns** — when and how to apply those skills

**Initial consultant set:**

#### orchestration-consultant
- Domain: agent coordination, team structures, parallel vs sequential execution
- Knows: `dispatching-parallel-agents`, `subagent-driven-development`
- Advises on: when tasks can safely run in parallel, when teams of agents are warranted,
  how to structure subagent dispatch for the current plan

#### version-control-consultant
- Domain: git workflows, branching strategy, worktrees, PRs
- Knows: `git-worktree-workflow`, `git-expert`, `github-expert`
- Advises on: when isolated worktrees are appropriate, when a branch suffices, PR strategy,
  commit granularity

#### planning-consultant
- Domain: design → spec → plan → implement cycles
- Knows: `brainstorming`, `writing-plans`, `executing-plans`
- Advises on: when a task needs a brainstorm/spec phase before implementation, when to use
  subagent-driven-development vs inline execution, how to sequence planning work

---

### Regional docs

One per top-level category. Replace `registry.md`.

**Location:** `dev-suite/<category>/REGION.md`

**Content:** Catalog of available skills in that region — name, purpose, when to use, what
it produces, how it chains. Written for the manager to quickly inventory available tools.

The manager reads only the regional docs for the regions task-analyser identified as relevant.

**Files to create:**
- `dev-suite/management/REGION.md`
- `dev-suite/planning/REGION.md`
- `dev-suite/coding/REGION.md`
- `dev-suite/research/REGION.md`

---

## File Structure

**New skills:**
```
dev-suite/management/orchestration/task-analyser/SKILL.md
dev-suite/management/orchestration/cheapskill/SKILL.md
dev-suite/management/orchestration/superskill/SKILL.md
dev-suite/management/orchestration/manager/SKILL.md
dev-suite/management/consultants/orchestration-consultant/SKILL.md
dev-suite/management/consultants/version-control-consultant/SKILL.md
dev-suite/management/consultants/planning-consultant/SKILL.md
```

**New regional docs:**
```
dev-suite/management/REGION.md
dev-suite/planning/REGION.md
dev-suite/coding/REGION.md
dev-suite/research/REGION.md
```

**Deleted:**
```
dev-suite/management/orchestration/simple-orchestrator/
dev-suite/management/orchestration/complex-orchestrator/
dev-suite/registry.md
```

---

## What Stays Unchanged

- All specialist skills (`git-expert`, `python-expert`, `rust-expert`, `typescript-expert`,
  `typst-expert`, `api-architect`, `docs-agent`, `research-agent`, `github-expert`)
- All quality skills (`tdd`, `systematic-debugging`, `verification-before-completion`,
  `requesting-code-review`, `receiving-code-review`, `simplify`)
- All planning skills (`brainstorming`, `writing-plans`, `executing-plans`)
- All management skills (`skill-manager`, `writing-skills`, `dispatching-parallel-agents`,
  `subagent-driven-development`)

---

## Updates Required

- `manifest.toml` — add entries for 4 new skills + 3 consultants; remove simple/complex-orchestrator
- `dev-suite/management/SKILL.md` dispatcher — update orchestration section to reference new skills
- `CLAUDE.md` — update registry reference (registry.md → regional docs), update orchestration notes
- `cf-check` — still works unchanged (walks SKILL.md files, checks against registry; registry.md
  reference needs updating to use regional docs, or cf-check is updated to check regional docs)

---

## Complexity Boundary Guidance

The task-analyser description field must make the simple/medium/difficult boundaries
unambiguous. Borderline cases default to the more capable path — routing to superskill
instead of cheapskill is cheap; routing to cheapskill when manager was needed is expensive.
