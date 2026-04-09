---
name: agent-manager
description: >
  Use when the user wants to see, manage, or understand their Claude Code skill
  setup — what skills are active globally, what is available in the current project,
  what is available in claudefiles but not installed, or when they want to install
  or remove skills for a specific scope.
---

# Agent Manager

Gives a complete picture of the Claude Code skill landscape and helps the user
manage what is installed where. Understands the difference between global scope
(all sessions) and project scope (this project only).

## Scopes

| Scope | Location | When active |
|-------|----------|-------------|
| Plugin | `~/.claude/plugins/` | All sessions, managed by plugin marketplace |
| Global | `~/.claude/skills/` | All sessions, manually installed |
| Project | `.claude/skills/` | This project only |

## On Invocation

Always run `cf-agents` first to get the current state:

```bash
cf-agents              # full overview
cf-agents --global     # global only
cf-agents --project    # project only
cf-agents --available  # what's in claudefiles but not installed
```

Present the output to the user before taking any action.

## Common Tasks

### "What skills do I have?"
```bash
cf-agents
```
Show the full output. Explain what each scope means if the user seems unfamiliar.

### "Install X skill for this project"
```bash
cd ~/projects/claudefiles && ./install.sh --project /path/to/project
```
This symlinks the full dev-suite into the project's `.claude/skills/` and adds
`.claudefiles/` to the project's `.gitignore`.

### "Install everything globally"
```bash
cd ~/projects/claudefiles && ./install.sh --user
```

### "Remove skills from this project"
```bash
cd ~/projects/claudefiles && ./install.sh --project /path/to/project --remove
```

### "What's available in claudefiles that I haven't installed?"
```bash
cf-agents --available
```

### "Set up this project from scratch"
```bash
cd ~/projects/claudefiles && ./install.sh --project /path/to/project
cf-init   # run inside the project to populate .claudefiles/ bus
```

## What Agent Manager Does NOT Do

- Does not manage marketplace plugins (superpowers, skill-creator etc.) — those are managed via Claude Code's plugin system
- Does not modify `~/.claude/settings.json` enabledPlugins — that's the plugin manager's job
- Does not create or edit skills — that's the skill-creator plugin's job

## Outputs

After any install/remove action, re-run `cf-agents` and show the updated state
so the user can confirm the change took effect.
