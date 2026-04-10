---
name: management
description: >
  Category dispatcher for orchestration and skill system tooling. Use when
  the task involves routing or triaging work (simple-orchestrator),
  planning a multi-skill workflow (complex-orchestrator), executing a plan
  with subagents in the current session (subagent-driven-development),
  dispatching independent parallel tasks (dispatching-parallel-agents),
  managing installed skills (meta/skill-manager), or authoring a new skill
  (meta/writing-skills). For design and implementation planning, use the
  planning category instead.
---

# Management

Routes to orchestration skills or skill system meta tooling.

## Orchestration skills

| Skill | Use when |
|-------|----------|
| `simple-orchestrator` | Start of any task — assesses complexity and routes |
| `complex-orchestrator` | Escalated tasks needing full multi-skill planning |
| `subagent-driven-development` | Executing a plan in the current session with subagents |
| `dispatching-parallel-agents` | Multiple independent tasks to run simultaneously |

## Meta skills

| Skill | Use when |
|-------|----------|
| `skill-manager` | Viewing, installing, or removing skills across scopes |
| `writing-skills` | Creating or editing a skill |
