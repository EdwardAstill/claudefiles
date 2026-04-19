---
name: coding
description: >
  Category dispatcher for coding work. Use when the task shape is "write,
  review, improve, debug, or version-control code" and the right specialist
  isn't yet chosen. Trigger phrases: "help me code this", "I need to build
  X", "review my code", "fix this bug", "set up CI", "design this API",
  "clean this up", "ship a feature". Routes into coding-quality (tdd,
  systematic-debugging, verification-before-completion, code-review,
  simplify), version-control (git-expert, github-expert,
  git-worktree-workflow), ci-cd (github-actions-expert), api-architect,
  system-architecture-expert, dsa-expert, or a language expert
  (python-expert, typescript-expert, rust-expert, typst-expert). Do NOT
  use as a leaf skill — always dispatch downward. Do NOT use for pure
  research or trade-off analysis (use research-agent) or for exploring an
  unfamiliar repo (use codebase-explainer).
---

# Coding

Routes to the right coding skill based on the task.

## Sub-categories and skills

| Skill | Use when |
|-------|----------|
| `tdd` | Writing new functionality — test-first |
| `systematic-debugging` | Bug or unexpected behaviour |
| `verification-before-completion` | Before marking any task done |
| `code-review` | Request a review or process review feedback |
| `simplify` | Code working but complex — reduce it |
| `regex-expert` | Mass search and replace, refactoring, text manipulation with sd/rg |
| `git-expert` | Git operations, worktrees, branching, merge, history |
| `github-expert` | GitHub — PRs, issues, browsing external repos |
| `github-actions-expert` | GitHub Actions workflows — write, debug, fix permissions/cache/matrix |
| `api-architect` | Designing or reviewing API contracts |
| `system-architecture-expert` | Application structure, service boundaries, layer design, scaling strategy |
| `dsa-expert` | Data structure/algorithm selection, complexity analysis, low-level design |
| `python-expert` | Python implementation, type checking, toolchain |
| `typescript-expert` | TypeScript/JS implementation, strict types |
| `rust-expert` | Rust implementation, ownership, cargo |
| `typst-expert` | Typst document authoring |
