# Automation Skills — Design Spec

**Date:** 2026-04-10
**Status:** Approved for implementation

**Depends on:** Tool management migration (dev-suite/ → skills/)

---

## Goal

A new `skills/management/automation/` subcategory with three skills covering
time-driven and event-driven execution: hooks, cron, and remote triggers.

---

## Architecture

```
skills/management/automation/
├── SKILL.md                    # dispatcher
├── hooks-setup/
│   └── SKILL.md
├── cron-agent/
│   └── SKILL.md
└── remote-trigger/
    └── SKILL.md
```

`skills/management/REGION.md` updated with entries for the 3 leaf skills.
The `automation/SKILL.md` dispatcher is not a leaf and does not get a REGION.md entry.
`skills/management/SKILL.md` dispatcher updated to reference the automation subcategory.

---

## Skills

### hooks-setup

**Frontmatter tools:** `["Read", "Edit"]` — actively edits hook configuration files.

**Critical constraint (prominent in skill body):** Hooks are configured by editing
`.claude/settings.json` (project) or `~/.claude/settings.json` (user) directly. There
is no `HookCreate` tool. This must be explicit.

**Content:**
- The 5 hook event types:
  - `PreToolUse` — fires before a tool call. **Non-zero exit blocks the tool.** Stdout
    surfaced to agent. Use for safety checks and validation.
  - `PostToolUse` — fires after. Stdout surfaced to agent. Use for logging, side-effects.
  - `Notification` — fires when Claude sends a notification.
  - `Stop` — fires when the main agent stops.
  - `SubagentStop` — fires when a subagent stops.
- Hook config location and format (JSON in settings.json)
- Common patterns:
  - Dangerous command safety check (PreToolUse on Bash tool)
  - Append bash commands to project audit log (PostToolUse)
  - Auto-run `cf check` after any SKILL.md edit (PostToolUse)
  - Notify on task completion (Stop)

### cron-agent

**Frontmatter tools:** `["Bash"]`

**Content:**
- `CronCreate`, `CronDelete`, `CronList` — all three. Always run `CronList` before
  creating to avoid duplicate scheduled jobs.
- Cron expression syntax (standard 5-field format)
- Headless mode: `claude -p "prompt"` for non-interactive execution
  - Requires `ANTHROPIC_API_KEY` or `CLAUDE_CODE_OAUTH_TOKEN` (`claude setup-token`)
  - `--allowedTools` to pre-approve tools
  - `--output-format json` for structured output
- Designing effective scheduled prompts: specific, scoped, include context the agent
  won't have (file paths, thresholds, output destinations)
- Common patterns:
  - Daily `cf brief --write` snapshot
  - Periodic `cf versions` check
  - Scheduled research summary
  - Weekly `cf doctor` health report

### remote-trigger

**Frontmatter tools:** `["Bash"]`

**Scope:** Covers the `RemoteTrigger` Claude Code tool only.

**Content:**
- `RemoteTrigger`: what it does, how to register and fire a trigger
- Wiring patterns:
  - CI post-job hook → trigger → Claude reviews results
  - Webhook receiver script → trigger → Claude processes event
  - Another script signals work is ready → Claude picks it up
- Prompt design: same principles as cron (specific, scoped)
- Auth: requires `CLAUDE_CODE_OAUTH_TOKEN` or API key
- Combining with hooks: trigger fires → Claude runs → PostToolUse hook notifies

---

### Dispatcher: automation/SKILL.md

**Frontmatter description:**
```
Subcategory dispatcher for automation skills. Use when the task involves setting up
event-driven execution (hooks-setup), scheduling recurring tasks (cron-agent), or
wiring external triggers to Claude Code (remote-trigger).
```

---

## manifest.toml

```toml
[skills.hooks-setup]
tools = ["Read", "Edit"]

[skills.cron-agent]
tools = ["Bash"]

[skills.remote-trigger]
tools = ["Bash"]
```

---

## Files

**Create:**
- `skills/management/automation/SKILL.md`
- `skills/management/automation/hooks-setup/SKILL.md`
- `skills/management/automation/cron-agent/SKILL.md`
- `skills/management/automation/remote-trigger/SKILL.md`

**Modify:**
- `manifest.toml` — add 3 skill entries
- `skills/management/REGION.md` — add hooks-setup, cron-agent, remote-trigger
- `skills/management/SKILL.md` — add automation subcategory section
