# Skills Reference

39 leaf skills across four categories. Run `af agents --tree` to see the live hierarchy.

---

## management/ — orchestration and tooling (11 skills)

### Orchestration

| Skill | Use when |
|-------|----------|
| `executor` | Every new task — default entry point |
| `manager` | Genuinely parallel multi-agent work |
| `subagent-driven-development` | Sequential plan execution with per-task review gates |

### Planning Advisors (loaded inline by manager)

| Skill | Single mandate |
|-------|---------------|
| `design-advisor` | Does this need brainstorming or a spec before coding? |
| `git-advisor` | What git strategy: worktrees, branches, PRs? |
| `coordination-advisor` | Parallel vs sequential? Dependency graph? |

### Meta

| Skill | Use when |
|-------|----------|
| `using-agentfiles` | Session start (automatic) |
| `skill-manager` | View, install, or remove skills |
| `skills` | Display the full skill catalog |
| `writing-skills` | Create or edit a SKILL.md |

---

## planning/ — design before implementation (2 skills)

| Skill | Use when |
|-------|----------|
| `brainstorming` | Requirements unclear — turn an idea into a spec |
| `writing-plans` | Spec approved — turn it into an implementation plan |

---

## coding/ — writing, reviewing, and shipping code (21 skills)

### Quality

| Skill | Use when |
|-------|----------|
| `tdd` | Writing new functionality — test-first |
| `systematic-debugging` | Bug, test failure, or unexpected behavior — find root cause first |
| `verification-before-completion` | Before marking any task done — mandatory in executor |
| `code-review` | Requesting or receiving a code review |
| `simplify` | Recently changed code is overly complex |
| `security-review` | OWASP top 10, injection vectors, auth/authz, dependency CVEs |
| `performance-profiling` | Code is correct but slow — measure before optimizing |
| `refactoring-patterns` | Large-scale restructuring (not small cleanups — that's simplify) |
| `dependency-management` | Version bumps, CVE scanning, breaking change analysis |
| `observability` | Structured logging, distributed tracing, metrics instrumentation |
| `accessibility` | WCAG 2.1 AA, semantic HTML, ARIA, keyboard navigation |

### Data

| Skill | Use when |
|-------|----------|
| `database-expert` | Schema design, migrations, query optimization, ORM patterns |

### Infrastructure

| Skill | Use when |
|-------|----------|
| `infrastructure-expert` | Dockerfiles, K8s, Terraform/Pulumi, cloud config, reverse proxies |

### Version Control

| Skill | Use when |
|-------|----------|
| `git-expert` | Git operations beyond basics — merge, bisect, reflog, history |
| `github-expert` | PRs, issues, Actions, browsing repos |
| `git-worktree-workflow` | Isolated feature work in a worktree |

### CI/CD

| Skill | Use when |
|-------|----------|
| `github-actions-expert` | GitHub Actions — write, debug, permissions, matrix, caching |

### API

| Skill | Use when |
|-------|----------|
| `api-architect` | Design or review API contracts — REST, GraphQL, RPC |

### Languages (toolchain + conventions specialists)

| Skill | Focus |
|-------|-------|
| `python-expert` | pyright LSP, uv, ruff, pytest — toolchain integration |
| `typescript-expert` | typescript-language-server LSP, bun, biome — toolchain integration |
| `rust-expert` | rust-analyzer LSP, cargo, clippy, rustfmt — toolchain integration |
| `typst-expert` | tinymist LSP, typst compile/watch — document authoring |

---

## research/ — information before action (5 skills)

| Skill | Answers | Use when |
|-------|---------|----------|
| `docs-agent` | "How do I use X?" | Need API signatures, config options, working examples |
| `research-agent` | "Should I use X?" | Evaluating trade-offs, risks, expert consensus |
| `codebase-explainer` | "How does this codebase work?" | Entering unfamiliar code, onboarding |
| `note-taker` | — | Creating notes, lessons, or interactive tutorials |
| `test-taker` | — | Answering questions from reference material |

---

## Invocation

**Inline (from executor):** `Skill("python-expert")` — loads skill patterns into the
current conversation. Preserves full session context.

**Slash command:** `/skill-name` — manual override when you know exactly what you want.

**Advisors** are loaded inline by manager during planning only. Never dispatched as
subagents.

**Specialists** are loaded inline by executor. Only dispatched as subagents when manager
needs parallel domain work.

---

## Adding a Skill

1. Create `agentfiles/<category>/[sub/]<skill-name>/SKILL.md` with frontmatter
2. Add entry to `manifest.toml` under `[skills.<skill-name>]`
3. Add entry to the category's `REGION.md`
4. Run `af check` to verify
5. Run `./install.sh --global` to pick up the new skill

```yaml
---
name: skill-name
description: >
  Use when [triggering conditions]. Under 1024 chars.
---
```
