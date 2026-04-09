# claudefiles

Personal Claude Code skill suite and tooling. Contains a coordinated set of skills for AI-driven development workflows, along with CLI tools and shared scripts.

## Skills

Skills live in `dev-suite/` and are organized into three categories. Run `cf-agents --tree` to see the full live hierarchy.

### management/ — orchestration and tooling

| Skill | Purpose |
|-------|---------|
| `simple-orchestrator` | Always-on triage — routes simple tasks directly, escalates complex ones |
| `complex-orchestrator` | Full planner — reads the registry, coordinates multi-skill workflows |
| `agent-manager` | Skill visibility and management — what's installed globally vs per-project |

### coding/ — writing, reviewing, and shipping code

| Skill | Purpose |
|-------|---------|
| `git-expert` | Version control manager — worktrees, branches, merge, cleanup |
| `github-expert` | GitHub and gh CLI specialist — PRs, issues, Actions, browsing external repos |
| `api-architect` | API design (from feature → contract) and review (existing code) |

### research/ — information before action

| Skill | Purpose |
|-------|---------|
| `docs-agent` | Technical reference lookup — exact APIs, examples, versioned docs |
| `research-agent` | General research and critical analysis — consensus, trade-offs, pitfalls |

The two orchestrators form a tiered system: `simple-orchestrator` activates on every task and either routes to a specialist or hands off to `complex-orchestrator` for full multi-skill coordination.

## Structure

```
claudefiles/
├── dev-suite/
│   ├── registry.md              ← skill contracts for complex-orchestrator
│   ├── management/              ← orchestration, planning, agent tooling
│   │   ├── SKILL.md             ← category dispatcher
│   │   ├── orchestration/
│   │   │   ├── simple-orchestrator/
│   │   │   └── complex-orchestrator/
│   │   └── agent-manager/
│   ├── coding/                  ← writing, reviewing, and shipping code
│   │   ├── SKILL.md             ← category dispatcher
│   │   ├── quality/             ← TDD, debugging, review (coming soon)
│   │   ├── version-control/
│   │   │   ├── git-expert/
│   │   │   └── github-expert/
│   │   └── api/
│   │       └── api-architect/
│   └── research/                ← information before action
│       ├── SKILL.md             ← category dispatcher
│       ├── docs-agent/
│       └── research-agent/
├── bin/                         ← personal CLI tools → ~/.local/bin/
├── lib/                         ← shared scripts used by multiple skills
├── manifest.toml                ← per-skill tool requirements + bin entries
└── install.sh                   ← install/remove skills and bin tools
```

## Install

### Quick start — full install from the local repo

```bash
./install.sh --global           # skills → ~/.claude/skills/, bin → ~/.local/bin/
./install.sh --local            # skills → ./.claude/skills/ (current project)
./install.sh --global --dry-run # preview without changes
./install.sh --global --remove  # remove installed symlinks
```

### Install from GitHub (no local clone required)

```bash
./install.sh --global --from github:EdwardAstill/claudefiles
./install.sh --local  --from github:EdwardAstill/claudefiles
```

Clones the repo to `~/.local/share/claudefiles-src/` on first run, then `git pull` on subsequent runs to stay current.

### Granular installs

```bash
# One category
./install.sh --global --category research
./install.sh --global --category coding
./install.sh --global --category management

# One skill by name
./install.sh --global --skill agent-manager
./install.sh --local  --skill git-expert
```

### Bootstrap — new machine, minimal first install

Install just `agent-manager` globally without cloning the whole repo:

```bash
curl -fsSL https://raw.githubusercontent.com/EdwardAstill/claudefiles/main/install.sh \
  | bash -s -- --global --from github:EdwardAstill/claudefiles --skill agent-manager
```

Then start a new Claude Code session. The agent-manager skill has everything it needs to install the rest from GitHub.

After any install, start a new Claude Code session. Skills appear automatically.

## CLI Tools

### `cf-worktree`

Creates a git worktree and opens a new terminal window with Claude Code running inside it.

```bash
cf-worktree <branch-name> [base-branch]

# Examples:
cf-worktree feature/auth-redesign
cf-worktree feature/auth-redesign main
```

Uses `$TERM_PROGRAM` (set by the terminal itself) to open a new window in the same terminal you're already running.

### `cf-status`

Shows the full repo branch/worktree topology map — trunk state, all branches, commits since each branch point, ahead/behind counts, dirty status, divergence warnings.

```bash
cf-status           # print to stdout
cf-status --write   # also save to .claudefiles/repo-map.md
```

### `cf-context`

Fingerprints the current project — language, runtime, package manager, framework, git state, key files. Run by any agent to orient itself instantly.

```bash
cf-context          # print to stdout
cf-context --write  # also save to .claudefiles/context.md
```

### `cf-versions`

Reads installed dependency versions from `package.json`, `Cargo.toml`, `go.mod`, `pyproject.toml`, lockfiles etc. Used by docs-agent to look up the right version of documentation.

```bash
cf-versions          # print to stdout
cf-versions --write  # also save to .claudefiles/versions.md
```

### `cf-routes`

Scans the codebase for API route definitions. Used by api-architect to map the full API surface without manually hunting through files. Supports Express, Fastify, Hono, Next.js, Axum, Actix-web, FastAPI, Go (net/http, chi, gin).

```bash
cf-routes           # print to stdout
cf-routes --write   # also save to .claudefiles/routes.md
```

### `cf-note`

Shared scratchpad for cross-agent communication. Agents append findings, decisions, or context to `.claudefiles/notes.md` so other agents can read them.

```bash
cf-note "discovered that auth uses JWT not sessions"
cf-note --agent research "rate limiting library: found consensus on token bucket approach"
cf-note --read       # print all notes
cf-note --clear      # clear notes (prompts for confirmation)
```

### `cf-agents`

Shows a complete inventory of Claude Code skills across all scopes — plugins, global user skills, and project-level skills — plus what's in claudefiles but not yet installed. Also invoke the `agent-manager` skill for Claude to help you act on what it shows.

```bash
cf-agents              # full overview
cf-agents --global     # global scope only (plugins + ~/.claude/skills/)
cf-agents --project    # current project scope only
cf-agents --available  # what's in claudefiles but not installed
```

### `cf-read`

Dumps the full `.claudefiles/` bus state in one call. Useful for agents to catch up on all shared context at once.

```bash
cf-read              # dump all bus files
cf-read context      # dump only context.md
cf-read notes        # dump only notes.md
cf-read repo-map     # dump only repo-map.md
```

### `cf-init`

Bootstraps `.claudefiles/` in the current project, adds it to `.gitignore`, and populates all bus files in one shot. Run at the start of a session.

```bash
cf-init              # full init
cf-init --dry-run    # preview without changes
```

## Agent Communication Bus

Each project gets a `.claudefiles/` folder at its root when any `--write` tool is run. This is the shared state layer between agents in a session.

```
.claudefiles/
├── context.md    ← cf-context output  (project fingerprint)
├── versions.md   ← cf-versions output (dependency versions)
├── routes.md     ← cf-routes output   (API surface map)
├── repo-map.md   ← cf-status output   (git topology)
└── notes.md      ← cf-note target     (free-form agent notes)
```

`.claudefiles/` should be gitignored — it's session state, not source. Add it to your `.gitignore`:

```
.claudefiles/
```

## Design Principles

### One file beats a wrapper

A script that lives in `scripts/` with a thin wrapper in `bin/` that just calls it is always worse than one file in the right place. Only split into two files when the CLI interface meaningfully differs from what the skill needs internally — different flags, different output format, or the bin tool combines multiple scripts.

If a script is useful as a CLI tool on its own, put it directly in `bin/`. If it's purely an internal detail of a skill, put it in `scripts/`. If it's both, `bin/` wins and the skill references it there.

### `scripts/` vs `bin/` vs `lib/`

| Location | Use when |
|----------|----------|
| `bin/` | Script is useful to run directly from the terminal |
| `dev-suite/<skill>/scripts/` | Script is an internal detail of one skill, not useful standalone |
| `lib/` | Script is shared across multiple skills but not a CLI tool |

## Adding a New Skill

1. Decide which category it belongs to: `management/`, `coding/`, or `research/`
2. Create `dev-suite/<category>/[sub-category/]<skill-name>/SKILL.md` with the standard frontmatter (`name`, `description`)
3. Add a `scripts/` folder inside the skill directory if it needs helper scripts
4. Add an entry to `manifest.toml` under `[skills.<skill-name>]` declaring required tools
5. Add an entry to `dev-suite/registry.md` with the skill's inputs, outputs, and chain targets
6. Re-run `./install.sh --user` (the symlink points to the live directory, so skills are picked up on next session)

## Adding a Bin Tool

1. Add the script to `bin/`
2. Make it executable: `chmod +x bin/<tool-name>`
3. Add its name to the `install` array in `manifest.toml` under `[bin]`
4. Re-run `./install.sh --user`

## Adding a Shared Library Script

Add scripts used by multiple skills to `lib/`. Reference them by absolute path or relative to the repo root. No install step needed — they're available via the symlinked directory.
