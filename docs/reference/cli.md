# CLI Tools Reference

All tools live in `bin/` and are symlinked to `~/.local/bin/` on install.

## cf-agents

Inventory of Claude Code skills across all scopes — plugins, global, project — plus CLI tool dependency status.

```bash
cf-agents              # full overview
cf-agents --global     # plugins + ~/.claude/skills/ only
cf-agents --project    # current project only
cf-agents --available  # what's in claudefiles but not installed
cf-agents --tree       # skill hierarchy tree
```

## cf-status

Full repo branch/worktree topology — trunk state, all branches, commits since branch point, ahead/behind, dirty status, divergence warnings.

```bash
cf-status           # print to stdout
cf-status --write   # also save to .claudefiles/repo-map.md
```

## cf-context

Fingerprints the current project — language, runtime, package manager, framework, git state, key files.

```bash
cf-context          # print to stdout
cf-context --write  # also save to .claudefiles/context.md
```

## cf-versions

Reads installed dependency versions from `package.json`, `Cargo.toml`, `go.mod`, `pyproject.toml`, lockfiles etc.

```bash
cf-versions          # print to stdout
cf-versions --write  # also save to .claudefiles/versions.md
```

## cf-routes

Scans the codebase for API route definitions. Supports Express, Fastify, Hono, Next.js, Axum, Actix-web, FastAPI, Go (net/http, chi, gin).

```bash
cf-routes           # print to stdout
cf-routes --write   # also save to .claudefiles/routes.md
```

## cf-note

Shared scratchpad for cross-agent communication. Agents append findings to `.claudefiles/notes.md`.

```bash
cf-note "message"
cf-note --agent research "message"
cf-note --read
cf-note --clear
```

## cf-read

Dumps the full `.claudefiles/` bus state in one call.

```bash
cf-read              # dump all bus files
cf-read context      # dump only context.md
cf-read notes        # dump only notes.md
cf-read repo-map     # dump only repo-map.md
```

## cf-init

Bootstraps `.claudefiles/` in the current project, adds it to `.gitignore`, and populates all bus files.

```bash
cf-init              # full init
cf-init --dry-run    # preview without changes
```

## cf-worktree

Creates a git worktree and opens a new terminal window with Claude Code running inside it. Uses `$TERM_PROGRAM` to detect the current terminal.

```bash
cf-worktree <branch-name> [base-branch]
```

## Adding a bin tool

1. Add the script to `bin/`
2. `chmod +x bin/<tool-name>`
3. Add its name to `manifest.toml` under `[bin] install = [...]`
4. Re-run `./install.sh --global`
