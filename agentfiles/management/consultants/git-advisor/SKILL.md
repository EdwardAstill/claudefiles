---
name: git-advisor
description: >
  Use when manager is deciding git strategy for multi-agent work. Trigger
  phrases: "worktree or branch", "should this be a worktree", "branching
  strategy for this", "how do we structure this in git", "commit directly or
  PR", "one PR or many", "how should agents share git state", "do parallel
  agents need isolation", "PR strategy for this plan", "commit structure for
  this work". Single mandate: answer "how should this work be structured in
  git?" Loaded inline by manager during planning — never dispatched as a
  subagent. Do NOT use for whether a plan needs design (use design-advisor),
  for task parallelisation (use coordination-advisor), or for actually executing
  a worktree workflow (use git-worktree-workflow).
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
