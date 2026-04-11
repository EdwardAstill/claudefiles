# claudefiles — Claude Code Guidance

This repo is the source of truth for a personal Claude Code skill suite. Skills are symlinked
into `~/.claude/skills/` (user-level) or `.claude/skills/` (project-level) via `cf install`.

## Slash Commands

Skills are nested under the `claudefiles/` prefix, so slash commands use the form
`/claudefiles:skill-name`. For example, `/claudefiles:git-expert` or
`/claudefiles:brainstorming`. These are the manual override — use them when you know
exactly what you want. Otherwise executor handles routing automatically.

For day-to-day use you don't need to type these — `using-claudefiles` fires at session
start and the system routes through executor automatically.

## Which Skill When

| Situation | Skill |
|-----------|-------|
| New task (default) | `executor` |
| New feature / component / design | `brainstorming` first, then executor |
| Bug or unexpected behaviour | `systematic-debugging` |
| Unfamiliar codebase | `codebase-explainer` |
| Implementation plan to execute | `writing-plans` → `subagent-driven-development` |
| Python / TypeScript / Rust / Typst work | `python-expert` / `typescript-expert` / `rust-expert` / `typst-expert` |
| API design or review | `api-architect` |
| Git operations / worktrees | `git-expert` / `git-worktree-workflow` |
| GitHub PRs, issues, Actions | `github-expert` / `github-actions-expert` |
| Look up library docs | `docs-agent` |
| Research trade-offs / risks | `research-agent` |
| Answer questions from reference material | `test-taker` |
| Write notes or interactive lessons | `note-taker` |
| Parallel multi-agent work | `manager` |
| Create or edit a skill | `writing-skills` |

## Key Facts

- **Skills live in** `skills/<category>/.../<skill-name>/SKILL.md` — four top-level categories: `management/`, `planning/`, `coding/`, `research/`
- **Each category has a dispatcher** at `skills/<category>/SKILL.md` that routes to the right leaf skill
- **Run `cf agents --tree`** to see the full live hierarchy
- **Regional docs live at** `skills/<category>/REGION.md` — the manager reads these during planning
- **Install with:** `cf install --global --source <clone-dir>` or run `./bootstrap.sh` for initial setup
- **Scripts:** `tools/scripts/` → symlinked to `~/.local/bin/` on install
- **Shared code:** `lib/` — available to any skill, no install step needed

## Skill File Format

```yaml
---
name: skill-name          # lowercase, hyphens only
description: >
  Use when [triggering conditions]. Keep under 1024 chars total.
  This is what Claude reads to decide whether to invoke the skill.
---
```

The description field is the only thing visible to other skills without invoking this
skill. Write it to be unambiguous about when to trigger.

## Regional Docs Sync Rule

**Any time a new leaf skill is added or removed, update the REGION.md for its category.**

Regional docs (`claudefiles/<category>/REGION.md`) are the skill catalogs the manager reads
during planning. Each entry uses `### skill-name` heading format. If they drift from
reality, the manager will mis-plan.

Run `cf-check` before committing any changes to `claudefiles/` to verify all leaf skills have
entries in their category's REGION.md.

## manifest.toml

Declares tool requirements per skill and which bin entries to install. Update it when:
- Adding a new skill with tool requirements
- Adding a new bin entry
- Changing a skill's tool requirements

```toml
[skills.skill-name]
tools = ["Bash", "Read"]   # Claude Code tool names
mcp = ["context7"]         # MCP server names (optional)

[bin]
install = ["cf-worktree"]  # files in bin/ to symlink to ~/.local/bin/
```

## Adding a New Skill — Checklist

- [ ] Decide which category it belongs to: `management/`, `planning/`, `coding/`, or `research/`
- [ ] Create `skills/<category>/[sub-category/]<skill-name>/SKILL.md` with valid frontmatter
- [ ] Add `scripts/` folder if the skill needs helper scripts
- [ ] Add entry to `manifest.toml` under `[skills.<skill-name>]`
- [ ] Add entry to the category's `skills/<category>/REGION.md` under `### skill-name`
- [ ] Re-run `cf install --global` if already installed (symlink picks it up on next session)

## Architecture Notes

**Two-path orchestration:**
- `executor` — default entry point for every new task. Orients with cf-context/cf-status, makes the routing decision inline (single agent or escalate to manager?), then handles the task end-to-end. Absorbs specialist skills inline (rust-expert, typescript-expert, api-architect, etc.) via the Skill tool — no subagent dispatch for specialisation.
- `manager` — for genuinely multi-agent work only: parallel domains, or scale that overwhelms a single context. Runs a single inline planning review pass (design? git strategy? coordination?), then dispatches agents. Consultants (planning-consultant, version-control-consultant, orchestration-consultant) are available but loaded only when the relevant decision is non-obvious.

**Specialists are skill libraries, not routing destinations.** python-expert, typescript-expert, rust-expert, api-architect, etc. are loaded inline by executor with `Skill("name")`. They are only dispatched as subagents when manager explicitly needs parallel domain work.

**Git expert outputs a WORKTREE CONTEXT block** — other skills should look for this when they need to know where to make changes.

**Skills are independent** — each skill works standalone. The orchestrators add coordination on top, they don't replace standalone use.

## Install Commands

`cf install` uses symlinks, not copies. Changes to skill files in this repo are immediately
reflected on the next Claude Code session — no re-install needed.

**Scopes:** `--global` installs to `~/.claude/skills/` + `~/.local/bin/`. `--local [path]`
installs to `<project>/.claude/skills/`. (`--project` is accepted as an alias for `--local`.)

**Granularity:** `--skill <name>` finds a skill by its SKILL.md `name` field (recursive
search through skills/). `--category <name>` installs a top-level category directory.
No flag installs the full skills/ directory as a single symlink.

**GitHub source:** Use `--source <clone-dir>` to install from a local clone, or run
`./bootstrap.sh` to clone and install in one step. The `bootstrap.sh` script clones to
`~/.local/share/claudefiles-src/` and installs skills via `cf install`.

**Scripts** are only symlinked on `--global` full install (no `--skill` or `--category` flags).
They live in `tools/scripts/` and are declared in `manifest.toml` under `[bin]`.

`cf install --remove` only removes symlinks created by `cf install`. It does not touch anything else.

The manifest TOML parser is a simple awk/grep pipeline — keep manifest.toml clean and
avoid unusual formatting (inline comments on value lines, multi-line arrays, etc.).
