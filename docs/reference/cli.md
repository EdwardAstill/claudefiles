# CLI Reference

The `af` CLI is a Python/Typer package at `tools/python/`. Install with
`uv tool install -e tools/python/` — editable, so source changes are live.

All commands use the form `af <subcommand>` (e.g., `af context`, `af status`).

---

## Context Tools

### af context

Fingerprint the current project — language, runtime, package manager, framework, git state.

```bash
af context             # print to stdout
af context --write     # also save to .agentfiles/context.md
```

### af status

Full repo branch/worktree topology — trunk, branches, commits, ahead/behind, dirty state.

```bash
af status              # print to stdout
af status --write      # also save to .agentfiles/repo-map.md
```

### af versions

Dependency versions from `package.json`, `Cargo.toml`, `pyproject.toml`, lockfiles, etc.

```bash
af versions            # print to stdout
af versions --write    # also save to .agentfiles/versions.md
```

### af routes

Scan codebase for API route definitions. Supports Express, Fastify, Hono, Next.js,
Axum, Actix-web, FastAPI, Go net/http, chi, gin.

```bash
af routes              # print to stdout
af routes --write      # also save to .agentfiles/routes.md
```

### af note

Shared scratchpad for cross-agent communication.

```bash
af note "message"              # append to .agentfiles/notes.md
af note --agent research "x"   # tag by agent
af note --read                 # read notes
af note --clear                # clear notes
```

### af read

Dump `.agentfiles/` bus state.

```bash
af read                # all bus files
af read context        # single file
af read notes
af read repo-map
```

### af init

Bootstrap `.agentfiles/` in the current project, populate all bus files.

```bash
af init                # full init
af init --dry-run      # preview
```

---

## Skill and Tool Management

### af agents

Full inventory of Claude Code skills and MCP servers across every scope.
Default output groups skills by category (derived from `manifest.toml`), with a compact
28-char-aligned column layout. Skills not in the manifest appear under `(uncategorized)`.

```bash
af agents              # full overview, grouped by category
af agents --tree       # deep skill hierarchy tree
af agents --global     # user-level skills only
af agents --project    # current project skills only
af agents --available  # in agentfiles but not installed
af agents --mcp        # MCP servers only
```

### af log

View skill invocation logs, session traces, and run periodic reviews.

```bash
af log                    # last 20 invocations
af log --tail 50          # last 50 entries
af log --skill tdd        # filter to one skill
af log --stats            # frequency table + escalation count
af log --escalations      # only sessions where executor handed off to manager
af log session            # timeline of latest session's tool calls
af log session --id XYZ   # timeline of specific session
af log analyze            # recovery pattern analysis of latest session
af log review --dry-run   # preview accumulated insights
af log review             # review, save to observations.md, clear logs
af log review --keep-stats  # clear sessions only, keep skill stats
```

See [logging reference](logging.md) for JSON schemas, file locations, and the review cycle.

### af test-skill

Scaffold a skill test workspace for benchmarking with the `skill-tester` skill.

```bash
af test-skill <name>    # first run: create evals.json template
                        # second run: create iteration workspace
```

See [docs/tools/test-skill.md](../tools/test-skill.md) for the full workflow.

### af check

Verify all leaf skills have entries in their category's REGION.md.

```bash
af check               # run verification
af check --verbose     # detailed output
```

### af setup

Check tool dependencies for skills installed in the current project.

```bash
af setup               # check all project skills
af setup --skills "python-expert,rust-expert"   # specific skills
af setup --write       # save report to .agentfiles/deps.md
```

### af tools

List all available tools — internal af subcommands and external CLI dependencies.

```bash
af tools               # human-readable list
af tools --json        # machine-readable for skills
```

---

## Secrets

### af secrets

Manages API keys and tokens stored at `~/.claude/secrets` (`KEY=value` format, chmod 600).
Never stored in any repo or project directory.

```bash
af secrets set ANNAS_API_KEY <key>     # store or update a key
af secrets get ANNAS_API_KEY           # print the value (raw, no label)
af secrets list                        # list key names only (never values)
af secrets remove ANNAS_API_KEY        # delete a key
af secrets env                         # print all as `export KEY=value` lines
af secrets exec -- <cmd> [args]        # run a command with all secrets injected
```

**Using a secret in a shell command:**
```bash
# Inline injection (one-off):
ANNAS_API_KEY=$(af secrets get ANNAS_API_KEY) anna download <md5>

# Inject all secrets then run:
af secrets exec -- anna download <md5>

# Export everything for the session:
eval $(af secrets env)
```

**File format** (`~/.claude/secrets`):
```
# comments are ignored
ANNAS_API_KEY=abc123
GITHUB_TOKEN=ghp_xxx
```

---

## Data Sources

### af index

Build a structural file tree for a directory and register it as a searchable data source.
Stores the tree in `~/.claude/data/<name>/tree.md` and ingests all markdown files into an
mks collection for full-text search. Multiple sources (notes, docs, codebases) can be indexed independently.

```bash
af index /path/to/dir                  # index as source named after the directory
af index /path/to/dir --name notes     # explicit name
af index --list                        # show all registered sources
af index --no-mks /path/to/dir         # tree only, skip mks ingestion
af index --files /path/to/dir          # show all files (default: dirs + leaf files)
af index --depth 3 /path/to/dir        # limit tree depth
af index --remove notes                # unregister a source
```

The tree shows directories with recursive file counts at every level, and lists individual
files only at leaf directories (dirs with no subdirs). Useful for orienting Claude to a
large file tree without reading every file.

Data store: `~/.claude/data/` — persistent across sessions, not tied to any project.

### af search

Search indexed data sources via mks (BM25 full-text + vector search).

```bash
af search --source notes calcium signalling     # search a specific source
af search complex analysis                      # search across all sources
af search --tree --source notes                 # show structural file tree
af search --list                                # list registered sources
af search --source notes --mode search topic    # BM25 only (fast)
af search --source notes --mode vsearch topic   # vector similarity (requires mks embed)
af search --source notes --snippets topic       # show text snippets in results
af search --source notes -n 20 topic            # max 20 results (default: 10)
```

**Search modes:**
| Mode | Speed | Quality | Requires |
|------|-------|---------|----------|
| `query` / `search` | Fast | BM25 keyword match | Nothing |
| `vsearch` | Medium | Semantic similarity | Ollama + `mks embed` |

Run `mks embed` after indexing to enable vector search. Requires [Ollama](https://ollama.ai) with `nomic-embed-text` pulled.

---

## Install

Full installer for skills, hooks, and CLI tools.

```bash
af install                               # full global install (default)
af install --skill git-expert            # one skill globally
af install --category research           # one category globally
af install --local /path/to/project      # project install
af install --remove                      # uninstall globally
af install --dry-run                     # preview
```

---

## Git

### af worktree

Create a git worktree and open a terminal with Claude Code.

```bash
af worktree <branch-name> [base-branch]
```

---

## UI Preview

### af preview

Serve HTML design mockups for visual iteration. Watches a directory for `.html`
files and serves the newest one, auto-refreshing the browser via SSE whenever a
new file appears.

```bash
af preview [DIRECTORY]           # default: /tmp/ui-preview
af preview --port 7823 /tmp/ui-preview/
af preview --no-open /tmp/ui-preview/   # don't auto-open browser
```

**How it works:**

1. Claude writes `.html` files to the watched directory (one per design option)
2. The browser auto-refreshes — no manual reload needed
3. User views options, then types their choice in the terminal

Files can be full HTML documents or bare content fragments. If the file doesn't
start with `<!DOCTYPE` or `<html`, the server wraps it in a Tailwind CDN shell
automatically — so Claude can write minimal fragments with no boilerplate.

**Implementation note:** Uses `ThreadingHTTPServer` so the SSE auto-refresh
connection doesn't block other requests.

```
/tmp/ui-preview/
  option-a.html      ← write here, browser shows it immediately
  option-b.html
  option-c.html
```

### af screenshot

Capture a browser screenshot that Claude can read visually to verify layout,
spacing, and colours after implementation.

```bash
af screenshot [URL]                         # default: http://localhost:3000
af screenshot http://localhost:3000 --out /tmp/shot.png
af screenshot http://localhost:3000 --mobile          # 390×844 (iPhone)
af screenshot http://localhost:3000 --full-page       # full scrollable height
af screenshot http://localhost:3000 --wait 500        # extra ms after load
af screenshot http://localhost:3000 --width 1440 --height 900
```

Uses Playwright with a headless Firefox backend. Firefox is installed
automatically on first run (`playwright install firefox`).

After capturing, Claude reads the PNG with the `Read` tool to visually verify
the rendered output matches the design spec.

## Logging & Analysis

### af log

Review skill invocations, session traces, and detected routing anomalies.

```bash
af log                    # last 20 invocations
af log --tail 50          # last 50 entries
af log --skill tdd        # filter to one skill
af log --stats            # frequency table + escalation count
af log --escalations      # sessions where executor → manager
af log --loops            # sessions with self-loops (skill called itself)
af log anomalies          # show detected routing anomalies
af log anomalies --clear  # show and delete anomalies log
af log session            # timeline of latest session
af log analyze [--id XYZ] # recovery patterns from session
af log review             # full review + append to observations.md
af log review --dry-run   # preview without clearing
```

Anomalies (detected automatically on Stop event):
- **self-loop**: skill invoking itself instead of escalating
- **chain depth > 3**: too many hops between skills (context loss)
- **wasted loads**: same skill invoked ≥3× in one session

See [docs/reference/logging.md](logging.md) for details.

---

## Communication Modes

### af caveman

Toggle persistent caveman mode across all sessions. Three levels + off.

```bash
af caveman on [LEVEL]     # enable: lite, full (default), actual-caveman
af caveman off            # disable
af caveman [status]       # show current state

# Examples:
af caveman on full        # max token save (~60-70%), slight quality dip
af caveman on lite        # light touch, no quality loss
af caveman on actual-caveman  # grunt-style cave talk (novelty)
af caveman                # show current mode
```

State file: `~/.claude/modes/caveman` (written via the unified `af mode` state dir; `af caveman` is a backwards-compat alias for `af mode on/off caveman`). UserPromptSubmit hook (`hooks/modes.py`) re-injects level reminder every turn (no drift over long conversations).

Modes:
- **off** — normal prose
- **lite** — drop filler, keep grammar (no quality loss)
- **full** — drop articles too, fragments OK, ~60–70% token save
- **actual-caveman** — grunt style with cave analogies (novelty only)

---

## Agent Communication Bus

`.agentfiles/` is gitignored session state shared between agents.

| File | Written by | Content |
|------|-----------|---------|
| `context.md` | `af context --write` | Project fingerprint |
| `repo-map.md` | `af status --write` | Git topology |
| `versions.md` | `af versions --write` | Dependency versions |
| `routes.md` | `af routes --write` | API surface map |
| `notes.md` | `af note` | Free-form findings |

Read all: `af read` / Single: `af read context`
