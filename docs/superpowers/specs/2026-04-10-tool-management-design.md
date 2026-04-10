# Tool Management System — Design Spec

**Date:** 2026-04-10
**Status:** Approved for implementation

---

## Goal

Unify all tools — bash scripts, Python API integrations, and external CLI dependencies — under a single `cf` command backed by a Python Typer package. Replace the fragmented `bin/` + `[cli.*]` manifest approach with a coherent structure that:

1. Works on a new machine with one command
2. Is easy to extend with new tools (add a Python module, register in `tools.json`)
3. Gives skills a single place to discover what tools are available and what they do

---

## Problem

The current setup has three separate systems with no unified interface:

- `bin/` — bash scripts symlinked to `~/.local/bin/`, each invoked as `cf-<name>`
- `[cli.*]` in `manifest.toml` — external tool registry, install-checked by `cf-agents`
- Ad-hoc Python/shell snippets inside bash scripts for JSON parsing

There is no single entrypoint. Skills reference tools as `cf-check`, `cf-agents` etc. — inconsistent with a future `cf github` or `cf browser`. Adding a complex API tool (one that needs HTTP, browser control, auth) has no clear home and no conventions to follow.

---

## Design

### Repository structure

```
tools/
  python/              # cf command — uv + Typer package
    src/cf/
      main.py          # app = typer.Typer(); registers all sub-apps
      lib.py           # shared utilities (git root, colour output)
      agents.py        # cf agents
      check.py         # cf check
      context.py       # cf context
      status.py        # cf status
      versions.py      # cf versions
      worktree.py      # cf worktree
      note.py          # cf note
      read.py          # cf read
      routes.py        # cf routes
      init.py          # cf init
      setup.py         # cf setup
      github.py        # cf github  (new)
      browser.py       # cf browser (new)
    pyproject.toml
  tools.json           # unified tool registry

skills/                # renamed from dev-suite/
  management/
  planning/
  coding/
  research/

lib/                   # kept during transition, ported to cf/lib.py as needed
bootstrap.sh           # 5-line entry point: clone + uv install + cf install
migrate.sh             # one-time migration script
```

`bin/` and `dev-suite/` are removed after migration.

---

### The `cf` command

One entrypoint installed globally via `uv tool install -e tools/python/`. Because it is installed in editable mode, edits to `.py` source files are live immediately — no reinstall needed. Exception: changes to `pyproject.toml` (new dependencies, new `[project.scripts]` entries) require re-running `uv tool install -e tools/python/`.

`pyproject.toml` declares a single script:
```toml
[project.scripts]
cf = "cf.main:app"
```

`main.py` imports each module and registers its Typer sub-app:
```python
import typer
from cf import agents, check, context, status, versions, worktree, note, read, routes, init, setup, github, browser

app = typer.Typer()
app.add_typer(agents.app,   name="agents")
app.add_typer(check.app,    name="check")
# etc.
```

Each module defines `app = typer.Typer()` and decorates its commands with `@app.command()`. Docstrings on each command serve as descriptions surfaced by `cf tools`.

Shared logic from `lib/common.sh` (git root detection, colour output, worktree helpers) is ported to `cf/lib.py` and imported by any module that needs it.

---

### Tool registry — `tools/tools.json`

Single source of truth for all tools — both `cf` subcommands and external dependencies. Replaces `[cli.*]` in `manifest.toml`.

**Internal tool entry:**
```json
{
  "name": "github",
  "type": "internal",
  "package": "cf",
  "description": "Interact with GitHub — list PRs, issues, create branches",
  "usage": "cf github <subcommand>"
}
```

**External tool entry:**
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

Fields: `name`, `type` (internal/external), `package`, `manager` (external only), `install` (optional override), `description`, `usage`, `examples` (optional).

---

### Tool discovery for skills

`tools.json` is bundled as package data inside the `cf` Python package (declared in `pyproject.toml` under `[tool.hatch.build.targets.wheel] include` or equivalent). The `cf tools` command reads it from the installed package location via `importlib.resources` — no dependency on the source repo path. This means `cf tools` works correctly whether the user installed from a local clone or via `bootstrap.sh`.

`cf tools` outputs all tools with their descriptions — install status included for external tools. Skills that need tool context call `cf tools` at their context-gathering step.

```
## Available Tools

### github  [internal]
Interact with GitHub — list PRs, issues, create branches
Usage: cf github <subcommand>

### qmd  [external — installed]
Local markdown search — BM25 + vector + LLM reranking
Usage: qmd <query> [--dir <path>]
```

`cf tools --json` returns machine-readable output. Adding a tool to `tools.json` makes it visible to all skills with no other changes required.

---

### Bootstrap and install

`bootstrap.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail
CLONE_DIR="$HOME/.local/share/claudefiles-src"
git clone https://github.com/EdwardAstill/claudefiles "$CLONE_DIR" 2>/dev/null \
  || git -C "$CLONE_DIR" pull --ff-only
# Migrate old ~/.claudefiles/ clone if present
[[ -d "$HOME/.claudefiles" && ! -L "$HOME/.claudefiles" ]] && echo "Note: old ~/.claudefiles/ clone detected — you can remove it after verifying bootstrap succeeded."
uv tool install -e "$CLONE_DIR/tools/python/"
export PATH="$(uv tool dir --bin):$PATH"
cf install --global "$@"
```

`cf install` (implemented in `cf/install.py`) handles:
- Installing the `cf` package itself is a prerequisite — `cf install` cannot run without `cf` already on PATH. `bootstrap.sh` ensures this by running `uv tool install` first and updating PATH before calling `cf install`.
- Symlinking `skills/` subdirectories to `~/.claude/skills/`
- Installing external tools from `tools.json`
- `--global` / `--local [path]` / `--skill <name>` / `--category <name>` / `--from <github:owner/repo>` flags
- `--dry-run`, `--remove`

The `--from github:owner/repo` flag clones (or pulls) the target repo to `~/.local/share/claudefiles-src/` and installs from there, matching the behaviour of the current `install.sh`.

Re-running `bootstrap.sh` pulls the latest and re-runs `cf install` — skills are symlinks so they update immediately.

---

### Migration

`migrate.sh` is a one-time script run before implementation begins:

1. `git mv dev-suite/ skills/`
2. `git mv bin/ tools/scripts/` (temporary; removed once bash scripts are ported)
3. Find-and-replace across all `skills/**/*.md`: `cf-check` → `cf check`, `cf-agents` → `cf agents`, etc.
4. Grep `skills/**/*.md` for any references to `lib/common.sh` or `lib/port-finder.sh` and flag them — these need manual review as `lib/` will be removed once ported to `cf/lib.py`
5. Update `CLAUDE.md` path references
6. Remove `[cli.*]` and `[bin]` sections from `manifest.toml`; leave `[skills.*]` entries in place

`[skills.*]` entries in `manifest.toml` (per-skill Claude Code tool requirements and MCP server declarations) are retained as-is — they are not replaced by `tools.json`. `tools.json` covers user-facing CLI tools; `manifest.toml` `[skills.*]` covers Claude Code internal tool permissions.

`tools/scripts/` is kept as a reference during the port. Bash scripts are deleted file-by-file as their Python equivalents are verified.

---

## Files

**Create:**
- `tools/python/pyproject.toml`
- `tools/python/src/cf/__init__.py`
- `tools/python/src/cf/main.py`
- `tools/python/src/cf/lib.py`
- `tools/python/src/cf/{agents,check,context,status,versions,worktree,note,read,routes,init,setup,github,browser}.py`
- `tools/tools.json`
- `migrate.sh`
- Updated `bootstrap.sh`

**Remove (after migration):**
- `bin/` (all files)
- `install.sh`

**Modify:**
- `manifest.toml` — remove `[bin]` and `[cli.*]` sections
- `CLAUDE.md` — update path references, `cf-*` → `cf *`
- `skills/**/*.md` — update tool references (via `migrate.sh`)
- `README.md` — already updated

---

## What this is not

- Not a replacement for skills — the `cf` command is the toolset skills invoke, not a skill itself
- Not a full rewrite of skill logic — porting bash scripts to Python is mechanical, the behaviour stays the same
- Not a new orchestration layer — `cf tools` is discovery only; task routing stays with `task-analyser`
