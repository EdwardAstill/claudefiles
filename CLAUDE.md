# claudefiles — Claude Code Guidance

This repo is the source of truth for a personal Claude Code skill suite (39 skills).
Skills are symlinked into `~/.claude/skills/` (user-level) or `.claude/skills/`
(project-level) via `install.sh`.

## Slash Commands

Skills use the form `/skill-name` (e.g., `/git-expert`, `/brainstorming`).
These are the manual override — use them when you know exactly what you want.
Otherwise executor handles routing automatically.

For day-to-day use you don't need to type these — `using-claudefiles` fires at
session start and the system routes through executor automatically.

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
| Database schema / migrations / queries | `database-expert` |
| Security audit | `security-review` |
| Performance issues | `performance-profiling` |
| Large-scale restructuring | `refactoring-patterns` |
| Docker / K8s / Terraform | `infrastructure-expert` |
| Dependency updates / CVE scanning | `dependency-management` |
| Logging / tracing / metrics | `observability` |
| Web accessibility | `accessibility` |
| Git operations / worktrees | `git-expert` / `git-worktree-workflow` |
| GitHub PRs, issues, Actions | `github-expert` / `github-actions-expert` |
| "How do I use X?" — API lookup | `docs-agent` |
| "Should I use X?" — trade-offs | `research-agent` |
| Answer questions from reference material | `test-taker` |
| Write notes or interactive lessons | `note-taker` |
| Parallel multi-agent work | `manager` |
| Create or edit a skill | `writing-skills` |

## Key Facts

- **Skills live in** `claudefiles/<category>/.../<skill-name>/SKILL.md` — four categories: `management/`, `planning/`, `coding/`, `research/`
- **Each category has a dispatcher** at `claudefiles/<category>/SKILL.md` that routes to the right leaf skill
- **Run `cf agents --tree`** to see the full live hierarchy
- **Regional docs** at `claudefiles/<category>/REGION.md` — the manager reads these during planning
- **Install:** `./install.sh --global` or `./bootstrap.sh` for new machines
- **CLI:** `cf <subcommand>` — Python CLI at `tools/python/src/cf/`, installed via `uv tool`

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

Run `cf check` before committing any changes to `claudefiles/` to verify all leaf skills have
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
```

## Adding a New Skill — Checklist

- [ ] Decide which category: `management/`, `planning/`, `coding/`, or `research/`
- [ ] Create `claudefiles/<category>/[sub-category/]<skill-name>/SKILL.md` with valid frontmatter
- [ ] Add `scripts/` folder if the skill needs helper scripts
- [ ] Add entry to `manifest.toml` under `[skills.<skill-name>]`
- [ ] Add entry to the category's `claudefiles/<category>/REGION.md` under `### skill-name`
- [ ] Run `./install.sh --global` (symlink picks it up on next session)

## Architecture Notes

**Two-path orchestration:**
- `executor` — default entry point for every new task. Orients with cf context/cf status, makes the routing decision inline, then handles the task end-to-end. Absorbs specialist skills inline via the Skill tool. Verification is MANDATORY before reporting completion. Escalates to manager with a structured HANDOFF CONTEXT block when parallel work is genuinely needed.
- `manager` — for genuinely multi-agent work only. Reads handoff context from executor, runs a planning review pass (design? git strategy? coordination?), dispatches agents, then reviews results with adaptive replanning if agents fail. Advisors (design-advisor, git-advisor, coordination-advisor) are loaded inline only when the relevant decision is non-obvious.

**Specialists are skill libraries, not routing destinations.** They are loaded inline by executor with `Skill("name")`. Only dispatched as subagents when manager explicitly needs parallel domain work.

**Git expert outputs a WORKTREE CONTEXT block** — other skills should look for this when they need to know where to make changes.

**Skills are independent** — each skill works standalone. The orchestrators add coordination on top, they don't replace standalone use.

## Install

**Single source of truth:** `install.sh` handles all install logic. Both `bootstrap.sh` and `cf install` delegate to it.

`install.sh` uses symlinks, not copies. Changes to skill files are immediately
reflected on the next Claude Code session — no re-install needed.

**Scopes:** `--global` installs to `~/.claude/skills/`. `--local [path]`
installs to `<project>/.claude/skills/`. (`--project` is accepted as an alias for `--local`.)

**Granularity:** `--skill <name>` finds a skill by its SKILL.md `name` field.
`--category <name>` installs one top-level category. No flag installs all skills
as individual symlinks (for slash command support).

**Other flags:** `--from github:owner/repo` clones from GitHub. `--dry-run` previews.
`--remove` uninstalls. `--list-categories` shows available categories.

The manifest TOML parser is a simple awk/grep pipeline — keep manifest.toml clean and
avoid unusual formatting (inline comments on value lines, multi-line arrays, etc.).
