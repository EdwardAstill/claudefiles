---
name: git-advisor
description: >
  Use when manager needs to decide git strategy for multi-agent work: whether to use
  worktrees, branches, or direct commits; PR strategy; commit structure. Single mandate:
  answer "how should this work be structured in git?" Loaded inline by manager during
  planning — never dispatched as a subagent.
---

# Git Advisor

Your only job: recommend the right git strategy for this plan — isolation level,
branching approach, PR strategy, and commit structure.

---

## Isolation level

**Use `git-worktree-workflow` when:**
- Work is a discrete feature running alongside other ongoing work
- Implementation risk could destabilise main mid-way
- Multiple agents working in parallel — each needs its own worktree
- Work spans multiple commits over an extended period

**Use a branch (no worktree) when:**
- Short-lived work with no parallel concerns
- Single agent, sequential commits

**Commit directly to main when:**
- Small fix, docs change, or single-file edit
- Solo project, low risk, completed in one sitting

## PR strategy

- Warrants review before merging → recommend `github-expert` for PR creation
- Direct merge is fine for small, safe changes on personal repos
- Each agent gets its own PR if they're working on independent features

## Commit structure

- One logical change per commit
- Frequent small commits during implementation
- Consider squashing before PR for cleaner history

## Skills to recommend

| Skill | When |
|-------|------|
| `git-worktree-workflow` | Feature work needing isolation; call at plan start and finish |
| `git-expert` | Complex git ops mid-workflow: conflict resolution, bisect, history rewrite |
| `github-expert` | PR creation, review, issue management |

---

## How to respond

Give concrete recommendations: name the approach, say where in the plan to apply it.
If multiple agents are involved, specify the isolation strategy for each.
