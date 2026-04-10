---
name: management
description: >
  Category dispatcher for orchestration and skill system tooling. Use when
  the task involves routing or triaging work (task-analyser), executing
  simple tasks cheaply (cheapskill), handling medium-complexity tasks as a
  capable general agent (superskill), planning and executing difficult
  multi-domain tasks (manager), executing a plan with subagents in the
  current session (subagent-driven-development), dispatching independent
  parallel tasks (dispatching-parallel-agents), managing installed skills
  (skill-manager), or authoring a new skill (writing-skills). For design
  and implementation planning, use the planning category instead.
---

# Management

Routes to orchestration skills or skill system meta tooling.

## Orchestration skills

| Skill | Use when |
|-------|----------|
| `task-analyser` | Entry point for every task — decomposes and routes by complexity |
| `cheapskill` | Simple tasks (1–2 subtasks, single domain, no coordination) |
| `superskill` | Medium tasks — capable general agent, full tool access |
| `manager` | Difficult tasks — multi-domain planning with consultants + subagent execution |
| `subagent-driven-development` | Executing a plan in the current session with subagents |
| `dispatching-parallel-agents` | Multiple independent tasks to run simultaneously |

## Consultant skills (planning phase only)

| Skill | Advises on |
|-------|-----------|
| `planning-consultant` | When brainstorm/spec is needed, sequencing planning work |
| `version-control-consultant` | Worktrees, branching strategy, PR structure |
| `orchestration-consultant` | Parallel vs sequential, team structures, subagent dispatch |

## Meta skills

| Skill | Use when |
|-------|----------|
| `skill-manager` | Viewing, installing, or removing skills across scopes |
| `writing-skills` | Creating or editing a skill |
