# claudefiles — Claude Code Guidance

This repo is the source of truth for a personal Claude Code skill suite. Skills are symlinked
into `~/.claude/skills/` (user-level) or `.claude/skills/` (project-level) via `install.sh`.

## Slash Commands

Any skill can be invoked directly with `/skill-name`. For example, `/git-expert` triggers
the git-expert skill immediately without waiting for simple-orchestrator to route it.

Slash commands are the manual override. The orchestrators are the automatic layer.
Skills should be designed to work both ways — invoked automatically by the orchestrator,
and invoked directly by the user when they know what they want.

## Key Facts

- **Skills live in** `dev-suite/<category>/.../<skill-name>/SKILL.md` — three top-level categories: `management/`, `coding/`, `research/`
- **Each category has a dispatcher** at `dev-suite/<category>/SKILL.md` that routes to the right leaf skill
- **Run `cf-agents --tree`** to see the full live hierarchy
- **Registry lives at** `dev-suite/registry.md` — the complex-orchestrator reads this
- **Install script:** `install.sh` (bash) — handles symlinks and `manifest.toml` parsing
- **Bin tools:** `bin/` → symlinked to `~/.local/bin/` on install
- **Shared scripts:** `lib/` — available to any skill, no install step needed

## Skill File Format

```yaml
---
name: skill-name          # lowercase, hyphens only
description: >
  Use when [triggering conditions]. Keep under 1024 chars total.
  This is what Claude reads to decide whether to invoke the skill.
---
```

The description field is the only thing visible to other skills and to simple-orchestrator
without invoking this skill. Write it to be unambiguous about when to trigger.

## Registry Sync Rule

**Any time a skill's inputs, outputs, or chain targets change, update `dev-suite/registry.md`.**

The registry is the contract between skills. If it drifts from reality, complex-orchestrator
will misplan. Keep it accurate.

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

- [ ] Decide which category it belongs to: `management/`, `coding/`, or `research/`
- [ ] Create `dev-suite/<category>/[sub-category/]<skill-name>/SKILL.md` with valid frontmatter
- [ ] Add `scripts/` folder if the skill needs helper scripts
- [ ] Add entry to `manifest.toml` under `[skills.<skill-name>]`
- [ ] Add entry to `dev-suite/registry.md` (inputs, outputs, chains)
- [ ] Re-run `./install.sh --user` if already installed (symlink picks it up on next session)

## Architecture Notes

**Two-tier orchestration:**
- `simple-orchestrator` — reads frontmatter only (already in context). Assesses complexity, routes or escalates. No file I/O.
- `complex-orchestrator` — reads `registry.md`. Plans multi-skill workflows. Only invoked by simple-orchestrator.

**Git expert outputs a WORKTREE CONTEXT block** — other skills should look for this when they need to know where to make changes.

**Skills are independent** — each skill works standalone. The orchestrators add coordination on top, they don't replace standalone use.

## Install Script Notes

`install.sh` uses symlinks, not copies. Changes to skill files in this repo are immediately
reflected on the next Claude Code session — no re-install needed.

**Scopes:** `--global` installs to `~/.claude/skills/` + `~/.local/bin/`. `--local [path]`
installs to `<project>/.claude/skills/`. (`--user` and `--project` are accepted as aliases.)

**Granularity:** `--skill <name>` finds a skill by its SKILL.md `name` field (recursive
search through dev-suite). `--category <name>` installs a top-level category directory.
No flag installs the full dev-suite as a single symlink.

**GitHub source:** `--from github:owner/repo` clones to `~/.local/share/claudefiles-src/`
(or pulls if already cached) and installs from there. The rest of the script is
source-agnostic — all path logic runs the same way after the clone step.

**Bin tools** are only symlinked on `--global` full dev-suite installs (no `--skill` or
`--category` flags). They live in `bin/` and are declared in `manifest.toml` under `[bin]`.

`--remove` only removes symlinks created by `install.sh`. It does not touch anything else.

The manifest TOML parser is a simple awk/grep pipeline — keep manifest.toml clean and
avoid unusual formatting (inline comments on value lines, multi-line arrays, etc.).
