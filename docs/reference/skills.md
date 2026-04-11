# Skills Reference

30 skills across four categories. Run `cf agents --tree` to see the live hierarchy with
invocation names.

---

## management/ — orchestration and tooling

### Orchestration

| Skill | Invoke as | Use when |
|-------|-----------|----------|
| `executor` | `claudefiles:executor` | Every new task — default entry point |
| `manager` | `claudefiles:manager` | Genuinely parallel multi-agent work |
| `subagent-driven-development` | `claudefiles:subagent-driven-development` | Sequential plan execution with per-task review gates |

### Planning advisors (loaded inline by manager)

| Skill | Invoke as | Single mandate |
|-------|-----------|---------------|
| `design-advisor` | `claudefiles:design-advisor` | Does this need brainstorming or a spec before coding? |
| `git-advisor` | `claudefiles:git-advisor` | What git strategy fits: worktrees, branches, PRs? |
| `coordination-advisor` | `claudefiles:coordination-advisor` | Parallel vs sequential? Dependency graph? |

### Meta

| Skill | Invoke as | Use when |
|-------|-----------|----------|
| `using-claudefiles` | `claudefiles:using-claudefiles` | Session start (automatic) |
| `skill-manager` | `claudefiles:skill-manager` | View, install, or remove skills |
| `writing-skills` | `claudefiles:writing-skills` | Create or edit a SKILL.md |

---

## planning/ — design before implementation

| Skill | Invoke as | Use when |
|-------|-----------|----------|
| `brainstorming` | `claudefiles:brainstorming` | Requirements unclear; design decisions not yet made |
| `writing-plans` | `claudefiles:writing-plans` | Implementation is complex enough to need a step-by-step plan |

---

## coding/ — writing, reviewing, and shipping code

### Quality

| Skill | Invoke as | Use when |
|-------|-----------|----------|
| `tdd` | `claudefiles:tdd` | Writing new functionality — test-first |
| `systematic-debugging` | `claudefiles:systematic-debugging` | Bug or unexpected behaviour |
| `verification-before-completion` | `claudefiles:verification-before-completion` | Before marking any task done |
| `code-review` | `claudefiles:code-review` | Requesting or receiving a code review |
| `simplify` | `claudefiles:simplify` | Code works but is overly complex |

### Version control

| Skill | Invoke as | Use when |
|-------|-----------|----------|
| `git-expert` | `claudefiles:git-expert` | Git operations: branching, merge, history, bisect |
| `git-worktree-workflow` | `claudefiles:git-worktree-workflow` | Feature work in an isolated worktree |
| `github-expert` | `claudefiles:github-expert` | GitHub: PRs, issues, browsing external repos |

### CI/CD

| Skill | Invoke as | Use when |
|-------|-----------|----------|
| `github-actions-expert` | `claudefiles:github-actions-expert` | GitHub Actions: write, debug, permissions, matrix |

### API

| Skill | Invoke as | Use when |
|-------|-----------|----------|
| `api-architect` | `claudefiles:api-architect` | Designing or reviewing API contracts |

### Languages

| Skill | Invoke as | Use when |
|-------|-----------|----------|
| `python-expert` | `claudefiles:python-expert` | Python: implementation, type checking, toolchain |
| `typescript-expert` | `claudefiles:typescript-expert` | TypeScript/JS: implementation, strict types |
| `rust-expert` | `claudefiles:rust-expert` | Rust: implementation, ownership, cargo |
| `typst-expert` | `claudefiles:typst-expert` | Typst: document authoring |

---

## research/ — information before action

| Skill | Invoke as | Use when |
|-------|-----------|----------|
| `docs-agent` | `claudefiles:docs-agent` | Library docs, API reference, versioned examples |
| `research-agent` | `claudefiles:research-agent` | Trade-offs, risks, consensus across sources |
| `codebase-explainer` | `claudefiles:codebase-explainer` | Unfamiliar codebase — execution paths, architecture |
| `note-taker` | `claudefiles:note-taker` | Writing structured notes or interactive lessons |
| `test-taker` | `claudefiles:test-taker` | Answering questions from reference material |

---

## Notes

**Invocation:** Use the Skill tool with the skill name (without `claudefiles:` prefix):
```
Skill("executor")
Skill("systematic-debugging")
Skill("rust-expert")
```

**Specialist skills are loaded inline by executor**, not dispatched as subagents.
They bring their patterns into the current conversation context, preserving session state.

**Advisors (design-advisor, git-advisor, coordination-advisor) are loaded inline by
manager** during the planning phase only. They are never dispatched as subagents.

**Adding a skill:** See CLAUDE.md → "Adding a New Skill — Checklist". Run `cf-check`
after any addition to verify REGION.md sync.
