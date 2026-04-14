---
name: management
description: >
  Category dispatcher for orchestration and skill system tooling. Use when the
  task involves single-agent execution (executor), multi-agent coordination (manager),
  sequential plan execution with review gates (subagent-driven-development),
  managing installed skills (agentfiles-manager), or authoring a skill (writing-skills).
  For design and implementation planning, use the planning category instead.
---

# Management

Routes to orchestration skills or skill system meta tooling.

## Orchestration skills

| Skill | Use when |
|-------|----------|
| `executor` | Default for every new task — orients, routes inline, handles end-to-end |
| `manager` | Genuinely multi-agent — parallel domains or scale that overwhelms one context |
| `subagent-driven-development` | Sequential plan execution with review gates per task |

## Advisors (manager planning phase — load the relevant one if needed)

| Skill | Advises on |
|-------|-----------|
| `design-advisor` | Whether brainstorming or a written spec is needed before implementation |
| `git-advisor` | Git strategy: worktrees, branching, PR approach, commit structure |
| `coordination-advisor` | Parallel vs sequential, dependency graph, team composition |

## Meta skills

| Skill | Use when |
|-------|----------|
| `using-agentfiles` | Session start — establishes that executor is the default entry point |
| `agentfiles-manager` | Viewing, installing, or removing skills across scopes |
| `writing-skills` | Creating or editing a skill |
