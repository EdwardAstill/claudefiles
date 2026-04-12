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
Default output groups skills by category (derived from `manifest.toml`), with a compact
28-char-aligned column layout. Skills not in the manifest appear under `(uncategorized)`.

```bash
cf agents              # full overview, grouped by category
cf agents --tree       # deep skill hierarchy tree
cf agents --global     # user-level skills only
cf agents --project    # current project skills only
cf agents --available  # in claudefiles but not installed
cf agents --mcp        # MCP servers only
```

### cf log

View the skill invocation log. Skills are recorded automatically by the
`hooks/skill-logger.py` PostToolUse hook whenever a `SKILL.md` is read.

```bash
cf log                 # last 20 invocations
cf log --tail 50       # last 50 entries
cf log --skill tdd     # filter to one skill
cf log --stats         # frequency table + escalation count
cf log --escalations   # only sessions where executor handed off to manager
```

Each entry records the skill name, session ID, the skill that was active before it
(`parent_skill`), and whether the session included an executor→manager escalation.

Log file: `~/.claude/logs/claudefiles.jsonl` — see [logging reference](logging.md) for the full system.

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

## Secrets

### cf secrets

Manages API keys and tokens stored at `~/.claude/secrets` (`KEY=value` format, chmod 600).
Never stored in any repo or project directory.

```bash
cf secrets set ANNAS_API_KEY <key>     # store or update a key
cf secrets get ANNAS_API_KEY           # print the value (raw, no label)
cf secrets list                        # list key names only (never values)
cf secrets remove ANNAS_API_KEY        # delete a key
cf secrets env                         # print all as `export KEY=value` lines
cf secrets exec -- <cmd> [args]        # run a command with all secrets injected
```

**Using a secret in a shell command:**
```bash
# Inline injection (one-off):
ANNAS_API_KEY=$(cf secrets get ANNAS_API_KEY) anna download <md5>

# Inject all secrets then run:
cf secrets exec -- anna download <md5>

# Export everything for the session:
eval $(cf secrets env)
```

**File format** (`~/.claude/secrets`):
```
# comments are ignored
ANNAS_API_KEY=abc123
GITHUB_TOKEN=ghp_xxx
```

---

## Data Sources

### cf index

Build a structural file tree for a directory and register it as a searchable data source.
Stores the tree in `~/.claude/data/<name>/tree.md` and registers a qmd collection for
full-text search. Multiple sources (notes, docs, codebases) can be indexed independently.

```bash
cf index /path/to/dir                  # index as source named after the directory
cf index /path/to/dir --name notes     # explicit name
cf index --list                        # show all registered sources
cf index --no-qmd /path/to/dir         # tree only, skip qmd registration
cf index --files /path/to/dir          # show all files (default: dirs + leaf files)
cf index --depth 3 /path/to/dir        # limit tree depth
cf index --remove notes                # unregister a source
```

The tree shows directories with recursive file counts at every level, and lists individual
files only at leaf directories (dirs with no subdirs). Useful for orienting Claude to a
large file tree without reading every file.

Data store: `~/.claude/data/` — persistent across sessions, not tied to any project.

### cf search

Search indexed data sources via qmd (BM25 + vector + LLM reranking).

```bash
cf search --source notes calcium signalling     # search a specific source
cf search complex analysis                      # search across all sources
cf search --tree --source notes                 # show structural file tree
cf search --list                                # list registered sources
cf search --source notes --mode search topic    # BM25 only (fast, no model needed)
cf search --source notes --mode vsearch topic   # vector similarity only
cf search --source notes --files topic          # return file paths only
cf search --source notes --full topic           # return full documents
cf search --source notes -n 20 topic            # max 20 results (default: 10)
```

**Search modes:**
| Mode | Speed | Quality | Requires |
|------|-------|---------|----------|
| `search` | Fast | Keyword match | Nothing |
| `vsearch` | Medium | Semantic similarity | Embeddings (`qmd embed`) |
| `query` | Slow | Best — hybrid + reranking | Model download (~640MB) |

The `query` mode (default) triggers a one-time model download on first use.

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
