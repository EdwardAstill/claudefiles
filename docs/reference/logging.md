# Logging Reference

Three files in `~/.claude/logs/` form the logging system for the claudefiles skill suite.
Together they support a monthly review-and-improve cycle.

---

## Files

### `claudefiles.jsonl` — Automated invocation log

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

View with `cf log`. Key signals to watch:
- **High escalation rate** (`cf log --escalations`) → executor routing is broken
- **Skills invoked <2× per month** (`cf log --stats`) → candidates for deletion
- **`parent_skill` always null** for a skill → it may never be called by the router

Session state files are kept in `~/.claude/logs/.sessions/` and cleaned up after 24 hours.

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

**Monthly (10–15 min):**

1. Run `cf log --stats` — spot skills invoked fewer than 2× that month (delete or merge?)
2. Run `cf log --escalations` — more than 2–3? Executor routing needs tightening
3. Read `observations.md` — move actionable items to `backlog.md`
4. Ask Claude to work through `backlog.md` items

**Thresholds worth acting on:**

| Signal | Threshold | Action |
|--------|-----------|--------|
| Skill invocations | <2/month | Delete or merge with another skill |
| Escalation rate | >5% of sessions | Review executor routing logic |
| Skills never called | 0 invocations | Delete unless intentionally dormant |

---

## `cf log` Reference

```bash
cf log                    # last 20 invocations
cf log --tail 50          # last 50 entries
cf log --skill tdd        # filter to one skill
cf log --stats            # frequency table + escalation count
cf log --escalations      # only sessions where executor → manager
```
