# Logging Reference

Three files, one directory, and a state folder in `~/.claude/logs/` form the logging system for the agentfiles skill suite.
Together they support session-level analysis and a monthly review-and-improve cycle.

---

## Files & Directories

### `agentfiles.jsonl` — Skill invocation log

Written by `hooks/skill-logger.py` (PostToolUse hook) whenever a `SKILL.md` is read.
One JSON line per invocation:

```json
{
  "ts": "2026-04-12T16:31:45Z",
  "skill": "python-expert",
  "session": "abc-123",
  "parent_skill": "executor",
  "escalated": false
}
```

| Field | What it means |
|-------|--------------|
| `ts` | UTC timestamp |
| `skill` | Skill that was invoked |
| `session` | Claude Code session ID |
| `parent_skill` | Last skill active before this one (proxy for caller) |
| `escalated` | `true` if executor handed off to manager in this session |

Key signals to watch:
- **High escalation rate** (`af log --escalations`) → executor routing is broken
- **Skills invoked <2× per month** (`af log --stats`) → candidates for deletion
- **`parent_skill` always null** for a skill → it may never be called by the router

---

### `sessions/` — Full session traces

Written by `hooks/skill-logger.py` for every tool call (not just skill reads).
Each session gets its own file: `~/.claude/logs/sessions/session-<id>.jsonl`.

Each line captures: timestamp, tool name, tool input, truncated output. Use for deep-dive analysis of what actually happened during a task.

#### `af log session [--id ID]`
Shows a condensed timeline of tool calls for the latest (or specified) session.

#### `af log analyze [--id ID]`
Scans the session log for recovery patterns (e.g., a failed test followed by a fix and a pass).

---

### `.sessions/` — Session state (ephemeral)

Tracks per-session state (last skill, skills seen, escalation flag). Cleaned up automatically after 24 hours.

---

### `observations.md` — Qualitative notes

A running log of patterns, routing misses, and things that felt off.
Written manually by you or by Claude during a session.

Format:
```
2026-04-12 — executor reached for manager on a single-file task; routing description too vague
2026-04-19 — python-expert and executor both handle uv commands; overlap worth investigating
```

When an observation becomes clearly actionable, move it to `backlog.md`.

---

### `backlog.md` — Improvement backlog

Actionable items to implement. Work through these periodically and delete when done.

Sections: Skills · Routing/Executor · Tooling/CLI · Docs · Unsorted

---

## Review Cycle

**The easy way — `af log review`:**

```bash
af log review --dry-run   # preview what it finds (no changes)
af log review             # review, append to observations.md, clear logs
af log review --keep-stats  # clear sessions but keep agentfiles.jsonl
```

This single command does everything: reads skill stats and session traces, surfaces patterns (low-usage skills, escalation rate, recovery patterns, context churn), appends the summary to `observations.md`, and clears the logs.

**When to run it:**
- Before creating or editing skills (the writing-skills skill reminds you)
- Monthly, or whenever session traces are piling up
- After a particularly rough debugging session

**The manual way (10–15 min):**

1. Run `af log --stats` — spot skills invoked fewer than 2× that month (delete or merge?)
2. Run `af log --escalations` — more than 2–3? Executor routing needs tightening
3. Read `observations.md` — move actionable items to `backlog.md`
4. Review `sessions/` for particularly difficult tasks and extract lessons
5. Ask Claude to work through `backlog.md` items
6. Clear session logs: `rm ~/.claude/logs/sessions/*.jsonl`

**Thresholds worth acting on:**

| Signal | Threshold | Action |
|--------|-----------|--------|
| Skill invocations | <2/month | Delete or merge with another skill |
| Escalation rate | >5% of sessions | Review executor routing logic |
| Skills never called | 0 invocations | Delete unless intentionally dormant |

---

## Maintenance & Cleanup

Session traces can grow large. The skill-logger automatically cleans up `.sessions/` state files older than 24 hours, but session traces in `sessions/` are kept until you delete them.

```bash
# Clear session traces (safe — stats log is separate)
rm ~/.claude/logs/sessions/*.jsonl

# Nuclear option — clear everything
rm -rf ~/.claude/logs/sessions/ ~/.claude/logs/.sessions/
```

`agentfiles.jsonl` is append-only and small. Generally doesn't need clearing.

---

## `af log` Reference

```bash
af log                    # last 20 invocations
af log --tail 50          # last 50 entries
af log --skill tdd        # filter to one skill
af log --stats            # frequency table + escalation count
af log --escalations      # only sessions where executor → manager
af log session            # timeline of latest session
af log session --id XYZ   # timeline of specific session
af log analyze            # recovery pattern analysis of latest session
af log review             # full review, append to observations.md, clear logs
af log review --dry-run   # preview review without clearing
af log review --keep-stats  # clear sessions only, keep skill stats
```
