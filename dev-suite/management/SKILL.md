---
name: management
description: >
  Category dispatcher for management and orchestration tasks. Use when the task
  involves planning a multi-step workflow, managing Claude Code agents and skills,
  or understanding the current agent setup. Routes to: simple-orchestrator (always-on
  triage), complex-orchestrator (full multi-skill planning), agent-manager (skill
  visibility and install management), or planning sub-skills.
---

# Management

Routes to the right management or orchestration skill based on the task.

## Sub-skills

| Skill | Use when |
|-------|----------|
| `simple-orchestrator` | Start of any task — assesses complexity and routes |
| `complex-orchestrator` | Escalated tasks needing full multi-skill planning |
| `agent-manager` | Viewing or managing installed skills across scopes |
| `planning/*` | Brainstorming, writing plans, executing plans (coming soon) |
