# claudefiles

Personal Claude Code skill suite and CLI toolset. Skills route tasks to the right specialist. The `cf` command provides tools for context gathering, git workflows, and external API integrations.

```bash
curl -fsSL https://raw.githubusercontent.com/EdwardAstill/claudefiles/main/bootstrap.sh | bash
```

---

## Structure

```
tools/
  python/          # cf command — uv + Typer package
    src/cf/
      main.py      # entrypoint
      agents.py    # cf agents
      check.py     # cf check
      context.py   # cf context
      status.py    # cf status
      versions.py  # cf versions
      worktree.py  # cf worktree
      note.py      # cf note
      read.py      # cf read
      routes.py    # cf routes
      init.py      # cf init
      setup.py     # cf setup
      github.py    # cf github
      browser.py   # cf browser
    pyproject.toml
  tools.json       # unified tool registry (internal + external)

skills/            # skill hierarchy — symlinked to ~/.claude/skills/ on install
  management/
  planning/
  coding/
  research/

lib/               # shared Python utilities
bootstrap.sh       # new machine entry point
migrate.sh         # one-time migration script
```

---

## The `cf` command

All tools are subcommands of a single `cf` Typer application. Install it once with `uv tool install -e tools/python/` and it stays live as you edit the source — no reinstall needed.

### Context tools

```bash
cf context           # fingerprint the current project — language, stack, framework, git state
cf context --write   # also save to .claudefiles/context.md

cf status            # full repo branch/worktree topology
cf status --write    # also save to .claudefiles/repo-map.md

cf versions          # dependency versions from package.json, Cargo.toml, pyproject.toml, etc.
cf versions --write  # also save to .claudefiles/versions.md

cf routes            # scan codebase for API route definitions
cf routes --write    # also save to .claudefiles/routes.md

cf read              # dump all .claudefiles/ bus state
cf read context      # single file
cf read notes

cf init              # bootstrap .claudefiles/ in current project, populate all bus files
cf init --dry-run

cf note "message"            # append to .claudefiles/notes.md
cf note --agent research "x" # tag by agent
cf note --read
cf note --clear
```

### Skill and tool management

```bash
cf agents              # full inventory: plugins, skills, MCP servers, tool status
cf agents --global     # global scope only
cf agents --project    # current project only
cf agents --tree       # skill hierarchy tree
cf agents --available  # in claudefiles but not installed

cf tools               # list all available tools with descriptions
cf tools --json        # machine-readable output for skills

cf check               # verify all leaf skills have entries in their category's REGION.md
cf check --verbose
```

### Git

```bash
cf worktree <branch> [base]  # create git worktree and open terminal with Claude Code
```

### API and automation

```bash
cf github <subcommand>   # GitHub — PRs, issues, branches, Actions
cf browser <subcommand>  # browser automation via Playwright — screenshot, scrape, navigate
```

---

## Tool registry — `tools/tools.json`

Single source of truth for all tools. Skills call `cf tools` to discover what's available.

**Internal tools** are subcommands of the `cf` package:

```json
{
  "name": "github",
  "type": "internal",
  "package": "cf",
  "description": "Interact with GitHub — list PRs, issues, create branches",
  "usage": "cf github <subcommand>"
}
```

**External tools** are installed via a package manager:

```json
{
  "name": "qmd",
  "type": "external",
  "manager": "bun",
  "package": "@tobilu/qmd",
  "description": "Local markdown search — BM25 + vector + LLM reranking, fully local",
  "usage": "qmd <query> [--dir <path>]",
  "examples": ["qmd 'authentication flow'", "qmd 'error handling' --dir src/"]
}
```

`cf agents` reads `tools.json` and checks PATH to report install status. `cf install` reads it to install missing tools.

---

## Skills

Skills live in `skills/` under four categories. Run `cf agents --tree` to see the live hierarchy.

| Category | Purpose |
|----------|---------|
| `management/` | Orchestration — task routing, planning, agent coordination |
| `planning/` | Brainstorming, spec writing, plan execution |
| `coding/` | Languages, git, APIs, quality (TDD, debugging, review) |
| `research/` | Docs lookup, general research |

### Orchestration

Every new task starts with `executor`. It orients with `cf context`/`cf status`, makes the routing decision inline, and handles the task end-to-end.

| Path | When |
|------|------|
| `executor` | Default — everything a single agent can handle (the common case) |
| `manager` | Genuinely parallel multi-agent work, or 20+ independent subtasks across unrelated domains |

Executor absorbs specialist skills inline (`Skill("rust-expert")`, `Skill("api-architect")`, etc.) — no subagent dispatch for specialisation.

### How skills discover tools

Skills call `cf tools` at the start of their context-gathering step to get a description of every available tool. For machine-readable use: `cf tools --json`. This means adding a new tool to `tools.json` makes it immediately visible to all skills — no skill files need to be updated.

### REGION.md

Each category has a `REGION.md` that catalogs its leaf skills. The `manager` skill reads these during planning. Run `cf check` before committing to verify all leaf skills have entries.

---

## Install

### New machine

```bash
curl -fsSL https://raw.githubusercontent.com/EdwardAstill/claudefiles/main/bootstrap.sh | bash
```

`bootstrap.sh` is a five-line script: clone the repo, run `uv tool install -e tools/python/`, then delegate to `cf install --global`.

### `cf install`

Full control over what gets installed and where.

| Flag | Installs to |
|------|-------------|
| `--global` | `~/.claude/skills/` |
| `--local [path]` | `<project>/.claude/skills/` |

| Flag | What |
|------|------|
| (none) | Full skills/ suite |
| `--category <name>` | One category |
| `--skill <name>` | One skill by its SKILL.md `name` field |

```bash
cf install --global                                        # full global install
cf install --global --from github:EdwardAstill/claudefiles # from GitHub
cf install --global --category research
cf install --global --skill git-expert
cf install --local /path/to/project
cf install --global --remove
cf install --global --dry-run
```

Skills are installed as symlinks — changes to skill files are live on the next Claude Code session, no reinstall needed.

### Update

```bash
bootstrap.sh   # re-running pulls latest (git pull --ff-only) and re-runs cf install
```

---

## Agent communication bus

Each project gets a `.claudefiles/` folder (gitignored) as shared state between agents.

| File | Written by | Purpose |
|------|-----------|---------|
| `context.md` | `cf context --write` | Project fingerprint — language, stack, framework |
| `repo-map.md` | `cf status --write` | Git topology — branches, worktrees, ahead/behind |
| `versions.md` | `cf versions --write` | Dependency versions for doc lookups |
| `routes.md` | `cf routes --write` | API surface map |
| `notes.md` | `cf note` | Free-form findings, decisions, context from any agent |

Run `cf init` to bootstrap all files at once.

---

## Adding a tool

**Internal (Python subcommand):**

1. Add `tools/python/src/cf/<name>.py` with a Typer app
2. Register it in `main.py`: `app.add_typer(<name>.app, name="<name>")`
3. Add an entry to `tools/tools.json` with `"type": "internal"`

**External:**

1. Add an entry to `tools/tools.json` with `"type": "external"` and install info

---

## Adding a skill

1. Decide which category: `management/`, `planning/`, `coding/`, or `research/`
2. Create `skills/<category>/[sub-category/]<skill-name>/SKILL.md` with `name` and `description` frontmatter
3. Add entry to `manifest.toml` under `[skills.<skill-name>]`
4. Add entry to the category's `skills/<category>/REGION.md` under `### skill-name`
5. Run `cf check` to verify
6. Run `cf install --global` if not already installed (symlink picks it up on next session)

---

## Skill file format

```yaml
---
name: skill-name
description: >
  Use when [triggering conditions]. Keep under 1024 chars total.
  This is what Claude reads to decide whether to invoke the skill.
---
```

The `description` field is the only thing visible to other skills without invoking the skill. Write it to be unambiguous about when to trigger.
