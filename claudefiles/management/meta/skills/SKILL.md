---
name: skills
description: >
  Use when the user wants to see all available claudefiles skills. Lists the full
  skill catalog grouped by category with invocation names and use cases.
---

# claudefiles Skills

Invoke any skill with `/claudefiles:<name>` or via the Skill tool.

## Management

| Skill | Use when |
|-------|----------|
| `claudefiles:executor` | Every new task — default entry point |
| `claudefiles:manager` | Genuinely parallel multi-agent work |
| `claudefiles:subagent-driven-development` | Sequential plan execution with per-task review gates |
| `claudefiles:using-claudefiles` | Session start (fires automatically) |
| `claudefiles:skill-manager` | View, install, or remove skills |
| `claudefiles:writing-skills` | Create or edit a skill |
| `claudefiles:skills` | This catalog |

### Planning advisors (loaded inline by manager)

| Skill | Single mandate |
|-------|---------------|
| `claudefiles:design-advisor` | Does this need brainstorming or a spec first? |
| `claudefiles:git-advisor` | What git strategy fits: worktrees, branches, PRs? |
| `claudefiles:coordination-advisor` | Parallel vs sequential? Dependency graph? |

## Planning

| Skill | Use when |
|-------|----------|
| `claudefiles:brainstorming` | Requirements unclear; design decisions not yet made |
| `claudefiles:writing-plans` | Complex implementation needing a step-by-step plan |

## Coding — Quality

| Skill | Use when |
|-------|----------|
| `claudefiles:tdd` | Writing new functionality — test-first |
| `claudefiles:systematic-debugging` | Bug or unexpected behaviour |
| `claudefiles:verification-before-completion` | Before marking any task done |
| `claudefiles:code-review` | Requesting or receiving a code review |
| `claudefiles:simplify` | Code works but is overly complex |

## Coding — Version Control & CI

| Skill | Use when |
|-------|----------|
| `claudefiles:git-expert` | Git operations: branching, merge, history |
| `claudefiles:git-worktree-workflow` | Feature work in an isolated worktree |
| `claudefiles:github-expert` | GitHub: PRs, issues, external repos |
| `claudefiles:github-actions-expert` | GitHub Actions: write, debug, fix workflows |

## Coding — Languages & API

| Skill | Use when |
|-------|----------|
| `claudefiles:python-expert` | Python implementation, type checking, toolchain |
| `claudefiles:typescript-expert` | TypeScript/JS implementation, strict types |
| `claudefiles:rust-expert` | Rust implementation, ownership, cargo |
| `claudefiles:typst-expert` | Typst document authoring |
| `claudefiles:api-architect` | Designing or reviewing API contracts |

## Research

| Skill | Use when |
|-------|----------|
| `claudefiles:docs-agent` | Library docs, API reference, versioned examples |
| `claudefiles:research-agent` | Trade-offs, risks, consensus across sources |
| `claudefiles:codebase-explainer` | Unfamiliar codebase — execution paths, architecture |
| `claudefiles:note-taker` | Writing structured notes or interactive lessons |
| `claudefiles:test-taker` | Answering questions from reference material |
