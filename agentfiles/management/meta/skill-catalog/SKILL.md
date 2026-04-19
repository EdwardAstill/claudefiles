---
name: skill-catalog
description: >
  Use when the user wants to browse the full list of available agentfiles
  skills. Trigger phrases: "what skills are available", "list all skills",
  "show me the skill catalog", "what can agentfiles do", "which skills exist",
  "browse the skill tree", "give me the full skill list", "what are all the
  skills I can invoke", "show me the catalogue", "what skills ship with
  agentfiles". Renders the catalog grouped by category with invocation names
  and one-line use cases. Do NOT use for viewing only installed skills in the
  current project (use agentfiles-manager), for writing a new skill (use
  writing-skills), or for manifest-consistency checks (use audit).
---

# agentfiles Skills

Invoke any skill with `/agentfiles:<name>` or via the Skill tool.

## Management

| Skill | Use when |
|-------|----------|
| `agentfiles:executor` | Every new task — default entry point |
| `agentfiles:manager` | Genuinely parallel multi-agent work |
| `agentfiles:subagent-driven-development` | Sequential plan execution with per-task review gates |
| `agentfiles:using-agentfiles` | Session start (fires automatically) |
| `agentfiles:agentfiles-manager` | View, install, or remove skills |
| `agentfiles:writing-skills` | Create or edit a skill |
| `agentfiles:skill-catalog` | This catalog |

### Planning advisors (loaded inline by manager)

| Skill | Single mandate |
|-------|---------------|
| `agentfiles:design-advisor` | Does this need brainstorming or a spec first? |
| `agentfiles:git-advisor` | What git strategy fits: worktrees, branches, PRs? |
| `agentfiles:coordination-advisor` | Parallel vs sequential? Dependency graph? |

## Planning

| Skill | Use when |
|-------|----------|
| `agentfiles:brainstorming` | Requirements unclear; design decisions not yet made |
| `agentfiles:writing-plans` | Complex implementation needing a step-by-step plan |

## Coding — Quality

| Skill | Use when |
|-------|----------|
| `agentfiles:tdd` | Writing new functionality — test-first |
| `agentfiles:systematic-debugging` | Bug or unexpected behaviour |
| `agentfiles:verification-before-completion` | Before marking any task done |
| `agentfiles:code-review` | Requesting or receiving a code review |
| `agentfiles:simplify` | Code works but is overly complex |

## Coding — Version Control & CI

| Skill | Use when |
|-------|----------|
| `agentfiles:git-expert` | Git operations: branching, merge, history |
| `agentfiles:git-worktree-workflow` | Feature work in an isolated worktree |
| `agentfiles:github-expert` | GitHub: PRs, issues, external repos |
| `agentfiles:github-actions-expert` | GitHub Actions: write, debug, fix workflows |

## Coding — Languages & API

| Skill | Use when |
|-------|----------|
| `agentfiles:python-expert` | Python implementation, type checking, toolchain |
| `agentfiles:typescript-expert` | TypeScript/JS implementation, strict types |
| `agentfiles:rust-expert` | Rust implementation, ownership, cargo |
| `agentfiles:typst-expert` | Typst document authoring |
| `agentfiles:api-architect` | Designing or reviewing API contracts |

## Research

| Skill | Use when |
|-------|----------|
| `agentfiles:docs-agent` | Library docs, API reference, versioned examples |
| `agentfiles:research-agent` | Trade-offs, risks, consensus across sources |
| `agentfiles:codebase-explainer` | Unfamiliar codebase — execution paths, architecture |
| `agentfiles:readrun` | Interactive Markdown docs (runnable Python + JSX visualisations) via the `rr` CLI |
| `agentfiles:test-taker` | Answering questions from reference material |
