---
name: management
description: >
  Category dispatcher for orchestration and skill-system tooling. Use when the
  user is asking about how agents are run, coordinated, or how the skill
  system itself is managed. Trigger phrases: "orchestrate this work",
  "dispatch agents", "run this task", "coordinate parallel work", "execute
  this plan step by step", "manage the skills in this repo", "write a new
  skill", "audit the skill system", "how should we structure this run",
  "skill-system meta question". Routes to executor, manager,
  subagent-driven-development, agentfiles-manager, writing-skills, audit, or
  the relevant planning advisor. Do NOT use for design or implementation
  planning itself (use the planning category), for coding-category tasks
  (use coding), or for information gathering (use research).
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
