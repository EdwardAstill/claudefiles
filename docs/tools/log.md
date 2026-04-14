# af log

View skill invocation logs, inspect session traces, and run periodic reviews.

**Source:** `tools/python/src/af/log.py`

## Quick start

```bash
af log                    # last 20 skill invocations
af log review --dry-run   # preview accumulated insights (no changes)
af log review             # review, save observations, clear logs
```

## How it works

Two hooks run on every tool call (configured via `hooks/install-hooks.sh`):

1. **Session trace** — every tool call (inputs + truncated output) is appended to `~/.claude/logs/sessions/session-<id>.jsonl`. These files grow fast but contain the raw history of what happened.

2. **Skill invocation log** — when a `SKILL.md` is read, the skill name, caller, and escalation status are appended to `~/.claude/logs/agentfiles.jsonl`. This is small and long-lived.

Category routers (directories like `coding/`, `management/` that just dispatch to child skills) are automatically excluded from the skill log.

## Commands

### Default view

```bash
af log                      # last 20 invocations
af log --tail 50            # last 50
af log --skill tdd          # filter to one skill
af log --stats              # frequency table + escalation count
af log --escalations        # only sessions where executor escalated to manager
```

| Flag | Description |
|------|-------------|
| `--skill <name>`, `-s` | Filter to specific skill |
| `--stats` | Frequency table sorted by invocation count |
| `--escalations`, `-e` | Only escalated sessions |
| `--tail <n>`, `-n` | Last N entries (default: 20) |

### `af log session`

Shows a condensed timeline of every tool call in a session.

```bash
af log session              # latest session
af log session --id abc123  # specific session
```

Output format:
```
[14:23:05] Read: /path/to/file.py
[14:23:08] Bash: pytest tests/ -v
[14:23:12] Edit: /path/to/file.py
```

### `af log analyze`

Scans a session for recovery patterns — a failed command followed by edits and a successful re-run.

```bash
af log analyze              # latest session
af log analyze --id abc123  # specific session
```

### `af log review`

The main maintenance command. Reads all accumulated logs, produces a structured summary, appends it to `~/.claude/logs/observations.md`, and clears the logs.

```bash
af log review               # full review + clear
af log review --dry-run     # preview without changes
af log review --keep-stats  # clear sessions but keep agentfiles.jsonl
```

**What it surfaces:**

| Pattern | What it means |
|---------|---------------|
| Low-usage skills (<=2 invocations) | Candidates for deletion or merging |
| Escalation rate >5% | Executor routing needs tightening |
| Skills loaded 3+ times in one session | Context churn — skill may be too narrow or too broad |
| Recovery patterns | Recurring failures that could be prevented by skill improvements |

**When to run it:**
- Before creating or editing skills (the `writing-skills` skill reminds you)
- Monthly, or when session traces are growing large
- After a rough debugging session to capture lessons

## Files

| Path | Contents | Grows? |
|------|----------|--------|
| `~/.claude/logs/agentfiles.jsonl` | Skill invocations (name, caller, escalation) | Slowly |
| `~/.claude/logs/sessions/session-*.jsonl` | Full tool call traces per session | Fast |
| `~/.claude/logs/.sessions/*.json` | Ephemeral session state (auto-cleaned after 24h) | No |
| `~/.claude/logs/observations.md` | Review summaries appended by `af log review` | Slowly |

## The review loop

```
Sessions accumulate logs automatically (via PostToolUse hook)
                    ↓
        af log review --dry-run
                    ↓
    See: which skills are unused, which cause churn,
         what keeps failing and getting fixed
                    ↓
    Fix the skill / merge it / delete it
                    ↓
            af log review
                    ↓
    Summary saved to observations.md, logs cleared
```

See `docs/reference/logging.md` for the full reference including JSON schemas, thresholds, and the manual review cycle.
