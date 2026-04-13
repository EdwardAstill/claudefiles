---
name: skill-manager
description: >
  Use when the user wants to set up skills for a project, see what is installed,
  install or remove skills, or understand their Claude Code skill setup. Also
  the entry point for new projects — invoke with "set up this project" or /setup.
---

# Skill Manager

The only skill installed globally. Everything else is installed per-project based
on what the project actually needs. Use `af agents` to inspect current state,
`install.sh` to install skills, and `af setup` to check tool dependencies.

## Scopes

| Scope | Location | When active |
|-------|----------|-------------|
| Plugin | `~/.claude/plugins/` | All sessions, managed by plugin marketplace |
| Global | `~/.claude/skills/` | All sessions — only skill-manager lives here |
| Project | `.claude/skills/` | This project only — skills installed per-project |

## Skill Hierarchy

All skills live in `~/.local/share/agentfiles-src/agentfiles/` (the home agentfiles install).
To see the full tree:

```bash
af agents --tree
```

Four categories:
- `management/` — orchestration (executor, manager, consultants), meta tooling (this skill + writing-skills)
- `planning/` — brainstorming, writing-plans, executing-plans
- `coding/` — quality, version control, language experts, API design
- `research/` — technical docs lookup, general research

## /setup — Set Up Skills for This Project

**Trigger:** user says "set up this project", "what skills do I need", or `/setup`

### Workflow

1. Run `af context --write` to fingerprint the project silently
2. Ask the user one question:

   > "Describe your project in a few sentences — what it does, what stack it uses, and what kind of work you'll be doing in it."

3. Based on their description, select skills using the mapping below
4. Present the selection clearly — what's being installed and why, what's being skipped and why
5. Wait for confirmation
6. Install each selected skill:
   ```bash
   ~/.local/share/agentfiles-src/install.sh --local --skill <name>
   ```
7. Run `af setup --write` to check tool dependencies and write `.agentfiles/deps.md`
8. If anything is missing, show the install commands prominently

### Skill Selection Mapping

| Signal in description | Install |
|----------------------|---------|
| Any project | `executor` |
| Git work, branches, parallel features, worktrees | `git-expert` |
| GitHub, PRs, CI, Actions, open source | `github-expert` |
| API design, endpoints, REST, GraphQL, contracts | `api-architect` |
| Unfamiliar libraries, SDKs, framework docs | `docs-agent` |
| Evaluating approaches, research, trade-offs, comparing options | `research-agent` |
| Python, FastAPI, Django, data science, ML | `python-expert` |
| TypeScript, JavaScript, React, Node, Next.js, Bun | `typescript-expert` |
| Rust, systems programming, WebAssembly, embedded | `rust-expert` |
| Typst, documents, papers, PDFs | `typst-expert` |

When in doubt, install it — skills are cheap to add and easy to remove.

### Example selection presentation

```
Based on your description, here's what I'll install:

  ✓  executor               handles every task end-to-end, routes inline
  ✓  git-expert             you mentioned working across multiple features in parallel
  ✓  docs-agent             unfamiliar libraries likely given the stack
  ✗  github-expert          skipping — you said this is a solo local project
  ✗  api-architect          skipping — no API work mentioned
  ✗  research-agent         skipping — not evaluating approaches, building something defined

Install these 4 skills? (yes / adjust)
```

## Checking Current State

```bash
af agents              # full overview — plugins, global, project, available, CLI deps
af agents --tree       # skill hierarchy tree
af agents --available  # what's in ~/.local/share/agentfiles-src but not installed here
```

## Installing and Removing Skills

```bash
# Install a skill into the current project
~/.local/share/agentfiles-src/install.sh --local --skill <name>

# Install a whole category
~/.local/share/agentfiles-src/install.sh --local --category research

# Remove
~/.local/share/agentfiles-src/install.sh --local --remove --skill <name>

# Preview
~/.local/share/agentfiles-src/install.sh --local --skill <name> --dry-run
```

## Checking Tool Dependencies

After installing skills, run `af setup` to check that all required CLI tools are present:

```bash
af setup           # check deps for all locally installed skills, print report
af setup --write   # also save report to .agentfiles/deps.md
```

If `bun` or `uv` is missing and skills require them, flag this prominently:

> "**mks is not installed** and is required by docs-agent and research-agent.
> Install it: `cargo install --path ~/projects/markstore`"

## CLI Tool Dependencies

Skills declare external CLI tool dependencies in `manifest.toml` under `[cli.<name>]`.

### Package managers

```bash
# bun — JavaScript runtime and package manager
curl -fsSL https://bun.sh/install | bash

# uv — Python package manager and tool runner
curl -LsSf https://astral.sh/uv/install.sh | sh

# cargo / rustup — Rust toolchain and package manager
curl https://sh.rustup.rs -sSf | sh
```

### Declaring a new CLI dependency

```toml
[cli.tool-name]
manager = "bun"           # or "uv"
package = "package-name"
description = "One-line description"
```

Then add `cli = ["tool-name"]` to the relevant `[skills.<name>]` entry.

## What Skill Manager Does NOT Do

- Does not manage marketplace plugins — those are managed via Claude Code's plugin system
- Does not create or edit skills — edit SKILL.md files directly in `~/.local/share/agentfiles-src/agentfiles/`
