# agentfiles

Personal Claude Code skill suite and CLI toolset. 40 skills route tasks to the right
specialist. The `af` CLI provides context gathering, git workflows, and skill management.

---

## Install

### New machine (recommended)

```bash
curl -fsSL https://raw.githubusercontent.com/EdwardAstill/agentfiles/main/bootstrap.sh | bash
```

This clones to `~/.local/share/agentfiles-src/`, bootstraps the `af` CLI and the
`agentfiles-manager` skill. After this, the `af` command is available.

To install all skills and CLI tools globally:

```bash
af install
```

### From a local clone

```bash
git clone https://github.com/EdwardAstill/agentfiles ~/.local/share/agentfiles-src
cd ~/.local/share/agentfiles-src
./install.sh                                 # bootstrap: af CLI + agentfiles-manager
af install                                   # install all skills + CLI tools
```

### Project-level install

```bash
af install --local /path/to/project
```

Symlinks skills into `<project>/.claude/skills/` and `<project>/.gemini/skills/`, and adds `.agentfiles/` to `.gitignore`.

### Update

Re-run `bootstrap.sh` — it pulls the latest and re-installs.

---

## How It Works

Every new task enters through **executor**, which orients with project context, handles
the task end-to-end, and loads specialist skills inline as needed. For genuinely parallel
multi-agent work, executor escalates to **manager**.

```
user message → executor → handles end-to-end (loads specialists inline)
                     └──→ manager (parallel agents, if needed)
```

Skills are loaded on demand — only names and descriptions are visible until invoked.
This keeps the context window clean while providing deep specialist knowledge when needed.

---

## Structure

```
agentfiles/           skill hierarchy (4 categories)
├── management/        orchestration, advisors, meta
├── planning/          brainstorming, implementation plans
├── coding/            languages, quality, git, CI/CD, API, data, infrastructure
└── research/          docs, research, codebase analysis, notes

tools/python/          af CLI — Python/Typer package
lib/                   shared shell utilities
install.sh             bootstrap: af CLI + agentfiles-manager
bootstrap.sh           new machine entry point (clone + bootstrap)
manifest.toml          per-skill tool requirements
```

See [docs/skill-tree.md](docs/skill-tree.md) for the full ASCII hierarchy.

---

## The `af` CLI

Installed via `uv tool install -e tools/python/`. Editable — source changes are
live immediately.

### Context tools

```bash
af context             # project fingerprint: language, stack, framework
af context --write     # also save to .agentfiles/context.md

af status              # full repo branch/worktree topology
af status --write      # also save to .agentfiles/repo-map.md

af versions            # dependency versions from lockfiles and manifests
af versions --write    # also save to .agentfiles/versions.md

af routes              # scan codebase for API route definitions
af routes --write      # also save to .agentfiles/routes.md

af read                # dump all .agentfiles/ bus state
af read context        # single file

af init                # bootstrap .agentfiles/ in current project
af init --dry-run

af note "message"              # append to .agentfiles/notes.md
af note --agent research "x"   # tag by agent
af note --read
af note --clear
```

### Skill and tool management

```bash
af agents              # full inventory: skills, MCP servers, tool status
af agents --tree       # skill hierarchy tree
af agents --global     # global scope only
af agents --project    # current project only
af agents --available  # in agentfiles but not installed

af tools               # list all available tools
af tools --json        # machine-readable

af check               # verify REGION.md entries for all leaf skills
af setup               # check tool dependencies for installed skills
```

### Install

```bash
af install                               # full global install (default)
af install --skill git-expert            # one skill globally
af install --category research           # one category globally
af install --local /path/to/project      # project-level install
af install --remove                      # uninstall globally
af install --dry-run                     # preview
```

### Git

```bash
af worktree <branch> [base]   # create worktree + open Claude Code
```

---

## Skills (48)

### Management (11)

| Skill | Use when |
|-------|----------|
| `executor` | Every new task — default entry point |
| `manager` | Genuinely parallel multi-agent work |
| `subagent-driven-development` | Sequential plan execution with review gates |
| `design-advisor` | Planning: does this need a spec first? |
| `git-advisor` | Planning: what git strategy? |
| `coordination-advisor` | Planning: parallel vs sequential agents? |
| `using-agentfiles` | Session start (automatic) |
| `agentfiles-manager` | View, install, or remove skills |
| `skills` | Display skill catalog |
| `writing-skills` | Create or edit a SKILL.md |
| `documentation-maintainer` | Sync docs after skill/CLI changes |

### Planning (2)

| Skill | Use when |
|-------|----------|
| `brainstorming` | Requirements unclear — idea to spec |
| `writing-plans` | Spec to implementation plan |

### Coding (30)

| Sub-category | Skill | Use when |
|-------------|-------|----------|
| **Languages** | `python-expert` | pyright LSP, uv, ruff, pytest |
| | `typescript-expert` | ts-language-server LSP, bun, biome |
| | `rust-expert` | rust-analyzer LSP, cargo, clippy |
| | `typst-expert` | tinymist LSP, typst compile |
| | `ui-expert` | React, Tailwind, shadcn/ui |
| | `tui-expert` | Terminal UIs (Textual, Ratatui, Ink) |
| **Quality** | `tdd` | Writing new functionality — test first |
| | `systematic-debugging` | Bug or unexpected behavior |
| | `verification-before-completion` | Before marking any task done |
| | `code-review` | Requesting or receiving review |
| | `simplify` | Recently changed code is complex |
| | `regex-expert` | Mass search and replace, refactoring |
| | `skill-tester` | Benchmark skills with rubric grading |
| | `security-review` | OWASP, CVEs, injection, auth |
| | `performance-profiling` | Correct but slow |
| | `refactoring-patterns` | Large-scale restructuring |
| | `dependency-management` | Version bumps, CVE scanning |
| | `observability` | Logging, tracing, metrics |
| | `accessibility` | WCAG 2.1 AA, ARIA, a11y |
| | `documentation` | READMEs, API docs, guides, changelogs |
| **Architecture** | `system-architecture-expert` | Service boundaries, scaling, layering |
| | `dsa-expert` | Data structures, algorithms, complexity |
| **Data** | `database-expert` | Schema, migrations, queries |
| | `file-converter` | PDF/image to markdown via cnv |
| **Infrastructure** | `infrastructure-expert` | Docker, K8s, Terraform |
| **Version control** | `git-expert` | Git operations beyond basics |
| | `github-expert` | PRs, issues, Actions |
| | `git-worktree-workflow` | Isolated feature work |
| **CI/CD** | `github-actions-expert` | GitHub Actions workflows |
| **API** | `api-architect` | API design and review |

### Research (5)

| Skill | Use when |
|-------|----------|
| `docs-agent` | "How do I use X?" — API lookup |
| `research-agent` | "Should I use X?" — trade-off analysis |
| `codebase-explainer` | "How does this codebase work?" |
| `note-taker` | Create notes or interactive lessons |
| `test-taker` | Answer questions from reference material |

---

## Agent Communication Bus

Each project gets a `.agentfiles/` folder (gitignored) for cross-agent state:

| File | Written by | Content |
|------|-----------|---------|
| `context.md` | `af context --write` | Project fingerprint |
| `repo-map.md` | `af status --write` | Git topology |
| `versions.md` | `af versions --write` | Dependency versions |
| `routes.md` | `af routes --write` | API surface map |
| `notes.md` | `af note` | Free-form findings |

Run `af init` to bootstrap all files at once.

---

## Logging and Skill Improvement

Every session logs skill usage and tool calls automatically via hooks. Over time
these logs reveal which skills are underused, which cause context churn, and what
keeps breaking and getting fixed.

### Review the logs

```bash
af log review --dry-run   # preview what it found (no changes)
af log review             # save summary to observations.md, clear logs
```

This surfaces: low-usage skills (delete or merge?), escalation rate (routing
broken?), skills loaded 3+ times in one session (context churn), and recovery
patterns (recurring failures).

### Act on the findings

Tell Claude to improve skills based on what the review found:

> "Review the observations in ~/.claude/logs/observations.md and improve the
> skills that are causing problems"

Or be specific:

> "The systematic-debugging skill is getting loaded 3 times per session — figure
> out why and fix it"

> "dsa-expert has only been used once — should we merge it into another skill?"

### Full reference

See [docs/reference/logging.md](docs/reference/logging.md) for JSON schemas,
thresholds, manual review steps, and all `af log` subcommands.

---

## Adding a Skill

1. Create `agentfiles/<category>/[sub/]<skill-name>/SKILL.md` with frontmatter
2. Add entry to `manifest.toml` under `[skills.<skill-name>]`
3. Add entry to the category's `REGION.md`
4. Run `af check` to verify
5. Run `af install` to pick up the new skill

```yaml
---
name: skill-name
description: >
  Use when [triggering conditions]. Under 1024 chars.
---
```

---

## Docs

| Document | Content |
|----------|---------|
| [docs/skill-tree.md](docs/skill-tree.md) | Full skill hierarchy + routing diagrams |
| [docs/reference/cli.md](docs/reference/cli.md) | CLI command reference |
| [docs/reference/browser.md](docs/reference/browser.md) | Browser automation (CDP) guide |
| [docs/reference/external-tools.md](docs/reference/external-tools.md) | External tools and LSPs registry |
| [docs/reference/install.md](docs/reference/install.md) | Install system reference |
| [docs/reference/orchestration.md](docs/reference/orchestration.md) | Routing architecture deep-dive |
| [docs/reference/skills.md](docs/reference/skills.md) | Complete skill catalog with invocation names |
| [docs/reference/workflows.md](docs/reference/workflows.md) | End-to-end workflow traces |
| [docs/reference/logging.md](docs/reference/logging.md) | Logging system, review cycle, `af log` reference |
| [docs/reference/agent-orchestration-patterns.md](docs/reference/agent-orchestration-patterns.md) | Research: agent routing, scaling, failure modes |
