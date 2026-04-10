# claudefiles — Claude Code Guidance

This repo is the source of truth for a personal Claude Code skill suite. Skills are symlinked
into `~/.claude/skills/` (user-level) or `.claude/skills/` (project-level) via `cf install`.

## Slash Commands

Any skill can be invoked directly with `/skill-name`. For example, `/git-expert` triggers
the git-expert skill immediately without waiting for task-analyser to route it.

Slash commands are the manual override. The task-analyser is the automatic layer.
Skills should be designed to work both ways — invoked automatically by the task-analyser,
and invoked directly by the user when they know what they want.

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

The description field is the only thing visible to other skills and to task-analyser
without invoking this skill. Write it to be unambiguous about when to trigger.

## Regional Docs Sync Rule

**Any time a new leaf skill is added or removed, update the REGION.md for its category.**

Regional docs (`dev-suite/<category>/REGION.md`) are the skill catalogs the manager reads
during planning. Each entry uses `### skill-name` heading format. If they drift from
reality, the manager will mis-plan.

Run `cf-check` before committing any changes to `dev-suite/` to verify all leaf skills have
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

**Three-path orchestration:**
- `task-analyser` — always-on entry point. Decomposes task, scores complexity across 3 signals, routes to one of three paths.
- `cheapskill` — haiku model, direct execution for simple tasks (1–2 subtasks, single domain, no coordination).
- `superskill` — Sonnet, capable general agent for medium tasks. Full tool access, tests own solution, absorbs specialist skills inline.
- `manager` — Opus, for difficult tasks. Planning phase: reads relevant REGION.md files + consults planning-consultant → version-control-consultant → orchestration-consultant. Execution phase: dispatches specialists as subagents.

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
