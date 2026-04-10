# Automation Skills — Design Spec

**Date:** 2026-04-10
**Status:** Approved for implementation

---

## Goal

A new `dev-suite/management/automation/` subcategory with three skills covering
time-driven and event-driven execution: hooks, cron, and remote triggers. Teaches Claude
how to build automated workflows that run without the user being present.

---

## Architecture

```
dev-suite/management/automation/
├── SKILL.md                    # dispatcher
├── hooks-setup/
│   └── SKILL.md
├── cron-agent/
│   └── SKILL.md
└── remote-trigger/
    └── SKILL.md
```

`management/REGION.md` updated with entries for the 3 leaf skills.
The `automation/SKILL.md` dispatcher is not a leaf skill and does not get a REGION.md entry.
`management/SKILL.md` dispatcher updated to reference the automation subcategory.

---

## Skills

### hooks-setup

**Frontmatter tools:** `["Read", "Edit"]` — this skill actively edits hook configuration
files, it is not a pure knowledge doc.

**Critical constraint (must be prominent in skill body):** Hooks are configured by editing
`.claude/settings.json` (project) or `~/.claude/settings.json` (user) directly. There is
no tool call for creating hooks. The skill must make this explicit to prevent agents from
trying a non-existent `HookCreate` tool.

**Content:**
- The 5 hook event types:
  - `PreToolUse` — fires before a tool call. **Non-zero exit blocks the tool.** Stdout
    is surfaced to the agent as context. Use for safety checks, validation, interception.
  - `PostToolUse` — fires after a tool call. Stdout surfaced to agent. Use for logging,
    notifications, side-effects.
  - `Notification` — fires when Claude sends a notification.
  - `Stop` — fires when the main agent stops.
  - `SubagentStop` — fires when a subagent stops.
- Hook config location and format (JSON in settings.json)
- Common patterns:
  - Dangerous command safety check before terminal tool use (PreToolUse)
  - Append every bash command to project audit log (PostToolUse)
  - Auto-run `cf-check` after any SKILL.md edit (PostToolUse)
  - Notify on task completion (Stop)
- How to write hook shell commands; how non-zero exit and stdout interact with the agent

### cron-agent

**Frontmatter tools:** `["Bash"]`

**Content:**
- `CronCreate`, `CronDelete`, `CronList` — all three. `CronList` is important: always
  list existing cron jobs before creating new ones to avoid duplicates.
- Cron expression syntax (standard 5-field format)
- Headless mode: `claude -p "prompt"` for non-interactive execution
  - Requires `ANTHROPIC_API_KEY` or `CLAUDE_CODE_OAUTH_TOKEN` (via `claude setup-token`)
  - `--allowedTools` to pre-approve tools without prompts
  - `--output-format json` for structured output in scripts
- Designing effective scheduled prompts:
  - Be specific about what to check and what to produce
  - Include context the agent won't have (file paths, thresholds, output destinations)
  - Keep scope narrow — scheduled tasks should be focused
- Common patterns:
  - Daily `cf-brief --write` snapshot
  - Periodic dependency version check with `cf-versions`
  - Scheduled research summary
  - Weekly `cf-doctor` health report

### remote-trigger

**Frontmatter tools:** `["Bash"]`

**Scope:** This skill covers the `RemoteTrigger` Claude Code tool specifically. Shell-based
file watchers (inotifywait, fswatch) are a separate primitive and out of scope.

**Content:**
- `RemoteTrigger` tool: what it does, how to register and fire a trigger
- Wiring patterns using RemoteTrigger:
  - CI post-job hook fires a trigger → Claude reviews results
  - Webhook receiver script fires a trigger → Claude processes the event
  - Another script signals work is ready → Claude picks it up
- Prompt design for triggered execution: same principles as cron (specific, scoped)
- Auth requirement: triggered execution requires `CLAUDE_CODE_OAUTH_TOKEN` or API key
- Combining with hooks: trigger fires → Claude runs → PostToolUse hook notifies

---

### Dispatcher: automation/SKILL.md

**Frontmatter description:**
```
Subcategory dispatcher for automation skills. Use when the task involves setting up
event-driven execution (hooks-setup), scheduling recurring tasks (cron-agent), or
wiring external triggers to Claude Code (remote-trigger).
```

Routes to the three leaf skills based on whether the automation is event-driven (hooks),
time-driven (cron), or externally-triggered (remote-trigger).

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
- `dev-suite/management/automation/SKILL.md`
- `dev-suite/management/automation/hooks-setup/SKILL.md`
- `dev-suite/management/automation/cron-agent/SKILL.md`
- `dev-suite/management/automation/remote-trigger/SKILL.md`

**Modify:**
- `manifest.toml` — add 3 skill entries
- `dev-suite/management/REGION.md` — add hooks-setup, cron-agent, remote-trigger
- `dev-suite/management/SKILL.md` — add automation subcategory section
