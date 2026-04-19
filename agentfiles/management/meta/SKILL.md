---
name: management-meta
description: >
  Sub-category dispatcher for skill-system tooling. Use when the task is about
  the skill system itself rather than about running work. Trigger phrases:
  "manage the skills in this project", "install or remove a skill", "write a
  new skill", "edit a skill", "audit the manifest", "sync the docs",
  "retrospective on recent sessions", "catalogue all skills", "skill-system
  housekeeping", "meta work on agentfiles". Routes to agentfiles-manager,
  writing-skills, audit, documentation-maintainer, retrospective, or
  skill-catalog. Do NOT use for orchestrating real work (use executor or
  manager), for design or planning (use planning category), or for running
  the catalog command directly (invoke skill-catalog).
---

# Management Meta

Routes to skill system tooling.

## Skills

| Skill | Use when |
|-------|----------|
| `agentfiles-manager` | Viewing, installing, or removing skills; setting up a new project |
| `writing-skills` | Creating a new skill or editing an existing one |
| `documentation-maintainer` | Syncing docs after skill/CLI changes |
| `audit` | Checking manifest consistency — missing entries, orphaned cli tools, PATH gaps |
