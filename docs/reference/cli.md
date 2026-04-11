# CLI Reference

The `cf` CLI is a Python/Typer package at `tools/python/`. Install with
`uv tool install -e tools/python/` — editable, so source changes are live.

All commands use the form `cf <subcommand>` (e.g., `cf context`, `cf status`).

---

## Context Tools

### cf context

Fingerprint the current project — language, runtime, package manager, framework, git state.

```bash
cf context             # print to stdout
cf context --write     # also save to .claudefiles/context.md
```

### cf status

Full repo branch/worktree topology — trunk, branches, commits, ahead/behind, dirty state.

```bash
cf status              # print to stdout
cf status --write      # also save to .claudefiles/repo-map.md
```

### cf versions

Dependency versions from `package.json`, `Cargo.toml`, `pyproject.toml`, lockfiles, etc.

```bash
cf versions            # print to stdout
cf versions --write    # also save to .claudefiles/versions.md
```

### cf routes

Scan codebase for API route definitions. Supports Express, Fastify, Hono, Next.js,
Axum, Actix-web, FastAPI, Go net/http, chi, gin.

```bash
cf routes              # print to stdout
cf routes --write      # also save to .claudefiles/routes.md
```

### cf note

Shared scratchpad for cross-agent communication.

```bash
cf note "message"              # append to .claudefiles/notes.md
cf note --agent research "x"   # tag by agent
cf note --read                 # read notes
cf note --clear                # clear notes
```

### cf read

Dump `.claudefiles/` bus state.

```bash
cf read                # all bus files
cf read context        # single file
cf read notes
cf read repo-map
```

### cf init

Bootstrap `.claudefiles/` in the current project, populate all bus files.

```bash
cf init                # full init
cf init --dry-run      # preview
```

---

## Skill and Tool Management

### cf agents

Full inventory of Claude Code skills and MCP servers across every scope.

```bash
cf agents              # full overview
cf agents --tree       # skill hierarchy tree
cf agents --global     # user-level only
cf agents --project    # current project only
cf agents --available  # in claudefiles but not installed
cf agents --mcp        # MCP servers only
```

### cf check

Verify all leaf skills have entries in their category's REGION.md.

```bash
cf check               # run verification
cf check --verbose     # detailed output
```

### cf setup

Check tool dependencies for skills installed in the current project.

```bash
cf setup               # check all project skills
cf setup --skills "python-expert,rust-expert"   # specific skills
cf setup --write       # save report to .claudefiles/deps.md
```

### cf tools

List all available tools — internal cf subcommands and external CLI dependencies.

```bash
cf tools               # human-readable list
cf tools --json        # machine-readable for skills
```

---

## Install

Delegates to `install.sh` — all args pass through verbatim.

```bash
cf install --global                      # full install
cf install --global --skill git-expert   # one skill
cf install --global --category research  # one category
cf install --local /path/to/project      # project install
cf install --global --remove             # uninstall
cf install --global --dry-run            # preview
```

---

## Git

### cf worktree

Create a git worktree and open a terminal with Claude Code.

```bash
cf worktree <branch-name> [base-branch]
```

---

## Agent Communication Bus

`.claudefiles/` is gitignored session state shared between agents.

| File | Written by | Content |
|------|-----------|---------|
| `context.md` | `cf context --write` | Project fingerprint |
| `repo-map.md` | `cf status --write` | Git topology |
| `versions.md` | `cf versions --write` | Dependency versions |
| `routes.md` | `cf routes --write` | API surface map |
| `notes.md` | `cf note` | Free-form findings |

Read all: `cf read` / Single: `cf read context`
