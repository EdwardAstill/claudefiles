# claudefiles

Personal Claude Code skill suite and CLI toolset. 39 skills route tasks to the right
specialist. The `cf` CLI provides context gathering, git workflows, and skill management.

```bash
curl -fsSL https://raw.githubusercontent.com/EdwardAstill/claudefiles/main/bootstrap.sh | bash
```

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
claudefiles/           skill hierarchy (4 categories)
├── management/        orchestration, advisors, meta
├── planning/          brainstorming, implementation plans
├── coding/            languages, quality, git, CI/CD, API, data, infrastructure
└── research/          docs, research, codebase analysis, notes

tools/python/          cf CLI — Python/Typer package
lib/                   shared shell utilities
install.sh             skill installer (single source of truth)
bootstrap.sh           new machine entry point
manifest.toml          per-skill tool requirements
```

See [docs/skill-tree.md](docs/skill-tree.md) for the full ASCII hierarchy.

---

## The `cf` CLI

Installed via `uv tool install -e tools/python/`. Editable — source changes are
live immediately.

### Context tools

```bash
cf context             # project fingerprint: language, stack, framework
cf context --write     # also save to .claudefiles/context.md

cf status              # full repo branch/worktree topology
cf status --write      # also save to .claudefiles/repo-map.md

cf versions            # dependency versions from lockfiles and manifests
cf versions --write    # also save to .claudefiles/versions.md

cf routes              # scan codebase for API route definitions
cf routes --write      # also save to .claudefiles/routes.md

cf read                # dump all .claudefiles/ bus state
cf read context        # single file

cf init                # bootstrap .claudefiles/ in current project
cf init --dry-run

cf note "message"              # append to .claudefiles/notes.md
cf note --agent research "x"   # tag by agent
cf note --read
cf note --clear
```

### Skill and tool management

```bash
cf agents              # full inventory: skills, MCP servers, tool status
cf agents --tree       # skill hierarchy tree
cf agents --global     # global scope only
cf agents --project    # current project only
cf agents --available  # in claudefiles but not installed

cf tools               # list all available tools
cf tools --json        # machine-readable

cf check               # verify REGION.md entries for all leaf skills
cf setup               # check tool dependencies for installed skills
```

### Install

```bash
cf install --global                      # full install (delegates to install.sh)
cf install --global --skill git-expert   # one skill
cf install --global --category research  # one category
cf install --local /path/to/project      # project-level install
cf install --global --remove             # uninstall
cf install --global --dry-run            # preview
```

### Git

```bash
cf worktree <branch> [base]   # create worktree + open Claude Code
```

---

## Skills (39)

### Management (11)

| Skill | Use when |
|-------|----------|
| `executor` | Every new task — default entry point |
| `manager` | Genuinely parallel multi-agent work |
| `subagent-driven-development` | Sequential plan execution with review gates |
| `design-advisor` | Planning: does this need a spec first? |
| `git-advisor` | Planning: what git strategy? |
| `coordination-advisor` | Planning: parallel vs sequential agents? |
| `using-claudefiles` | Session start (automatic) |
| `skill-manager` | View, install, or remove skills |
| `skills` | Display skill catalog |
| `writing-skills` | Create or edit a SKILL.md |

### Planning (2)

| Skill | Use when |
|-------|----------|
| `brainstorming` | Requirements unclear — idea to spec |
| `writing-plans` | Spec to implementation plan |

### Coding (21)

| Sub-category | Skill | Use when |
|-------------|-------|----------|
| **Languages** | `python-expert` | pyright LSP, uv, ruff, pytest |
| | `typescript-expert` | ts-language-server LSP, bun, biome |
| | `rust-expert` | rust-analyzer LSP, cargo, clippy |
| | `typst-expert` | tinymist LSP, typst compile |
| **Quality** | `tdd` | Writing new functionality — test first |
| | `systematic-debugging` | Bug or unexpected behavior |
| | `verification-before-completion` | Before marking any task done |
| | `code-review` | Requesting or receiving review |
| | `simplify` | Recently changed code is complex |
| | `security-review` | OWASP, CVEs, injection, auth |
| | `performance-profiling` | Correct but slow |
| | `refactoring-patterns` | Large-scale restructuring |
| | `dependency-management` | Version bumps, CVE scanning |
| | `observability` | Logging, tracing, metrics |
| | `accessibility` | WCAG 2.1 AA, ARIA, a11y |
| **Data** | `database-expert` | Schema, migrations, queries |
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

## Install

### New machine

```bash
curl -fsSL https://raw.githubusercontent.com/EdwardAstill/claudefiles/main/bootstrap.sh | bash
```

Clones to `~/.local/share/claudefiles-src/`, installs the `cf` CLI via `uv tool`,
then runs `install.sh --global` for skills.

### From a local clone

```bash
git clone https://github.com/EdwardAstill/claudefiles ~/.local/share/claudefiles-src
cd ~/.local/share/claudefiles-src
uv tool install --force -e tools/python/    # install cf CLI
./install.sh --global                        # install skills
```

### Project-level install

```bash
./install.sh --local /path/to/project
```

Symlinks skills into `<project>/.claude/skills/` and adds `.claudefiles/` to `.gitignore`.

### Update

Re-run `bootstrap.sh` — it pulls the latest and re-installs.

---

## Agent Communication Bus

Each project gets a `.claudefiles/` folder (gitignored) for cross-agent state:

| File | Written by | Content |
|------|-----------|---------|
| `context.md` | `cf context --write` | Project fingerprint |
| `repo-map.md` | `cf status --write` | Git topology |
| `versions.md` | `cf versions --write` | Dependency versions |
| `routes.md` | `cf routes --write` | API surface map |
| `notes.md` | `cf note` | Free-form findings |

Run `cf init` to bootstrap all files at once.

---

## Adding a Skill

1. Create `claudefiles/<category>/[sub/]<skill-name>/SKILL.md` with frontmatter
2. Add entry to `manifest.toml` under `[skills.<skill-name>]`
3. Add entry to the category's `REGION.md`
4. Run `cf check` to verify
5. Run `./install.sh --global` to pick up the new skill

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
| [docs/reference/install.md](docs/reference/install.md) | Install system reference |
| [docs/reference/orchestration.md](docs/reference/orchestration.md) | Routing architecture deep-dive |
| [docs/reference/skills.md](docs/reference/skills.md) | Complete skill catalog with invocation names |
| [docs/reference/workflows.md](docs/reference/workflows.md) | End-to-end workflow traces |
| [docs/reference/agent-orchestration-patterns.md](docs/reference/agent-orchestration-patterns.md) | Research: agent routing, scaling, failure modes |
