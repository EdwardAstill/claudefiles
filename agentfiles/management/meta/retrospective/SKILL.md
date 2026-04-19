---
name: retrospective
description: >
  Use when analysing session logs to surface routing failures, self-loops,
  wasted skill loads, and recovery patterns — then apply fixes to skills,
  hooks, and CLI tooling. Trigger phrases: "run a retrospective", "review
  session logs", "why did the session feel loopy", "af log looks weird",
  "which skills are firing too often", "find routing failures in recent
  sessions", "weekly skill system review", "analyse af log stats", "the skill
  system feels off", "self-improvement pass on skills". Do NOT use for
  one-shot manifest integrity checks (use audit), for syncing docs after a
  known rename (use documentation-maintainer), or for authoring a new skill
  from scratch (use writing-skills).
---

# Retrospective

Analyze session logs → surface problems → fix skills/hooks/tools. This is how the
skill system improves itself.

## When to run

- After a session felt slow or loopy
- Weekly/monthly maintenance
- After adding or changing skills
- When `af log --stats` shows anomalies

## Step 1: Gather data

```bash
af log --stats                    # skill frequency table
af log --escalations              # sessions where executor → manager
af log -n 50                      # recent invocations with parent chains
af log review --dry-run           # full analysis without clearing logs
```

## Step 2: Identify problems

Look for these patterns in the output:

### Self-loops (CRITICAL)
A skill calling itself (`parent_skill == skill`). Means the skill didn't resolve
the task and re-invoked itself instead of escalating or completing.

```bash
af log --loops                    # show self-loop entries
```

**Fix:** Open the looping skill's SKILL.md. Add explicit completion criteria or
escalation rules so it doesn't re-invoke itself.

### Long routing chains (depth > 3)
Skill A → B → C → D → E. Each hop loses context and burns tokens.

**Fix:** The first skill in the chain probably shouldn't have delegated. Either:
- Broaden its scope to handle the work inline
- Add the missing domain to executor's specialist list

### Circular routing (A → B → ... → A)
Skills bouncing back to already-visited skills.

**Fix:** The chain had no skill that could actually do the work. Either:
- A needed skill is missing — create it
- An existing skill's description doesn't match what it can do — fix it

### High escalation rate (> 5%)
Executor is escalating to manager too often.

**Fix:** Review what triggered escalation. Usually executor can handle it inline —
tighten the escalation criteria in executor SKILL.md.

### Wasted skill loads (3+ loads in one session)
Same skill loaded repeatedly. Context churn — the skill keeps getting re-read
without making progress.

**Fix:** The skill is either too narrow (can't finish the job) or too broad
(gets loaded for things it can't do). Refine its description.

## Step 3: Apply fixes

For each problem found:

1. **Read the affected skill** — understand what it currently says
2. **Read the log entries** — understand what actually happened
3. **Edit the skill** — add guardrails, clarify scope, fix routing
4. **If the problem is in hooks** — edit the hook script (e.g., skill-logger.py)
5. **If the problem is in CLI** — edit the af tool source
6. **If a skill is missing** — create it with the writing-skills skill

## Step 4: Record findings

```bash
af log review                     # append findings to observations.md, clear logs
```

Or manually update:
- `~/.claude/logs/observations.md` — patterns noticed
- `~/.claude/logs/backlog.md` — actionable fixes not yet done

## Step 5: Verify

After applying fixes, check:
- Changed skills still parse correctly (YAML frontmatter valid)
- Hook scripts still run (`python3 -c "import skill_logger"` etc.)
- `af log --stats` baseline is clean

## Key files

| File | Purpose |
|------|---------|
| `~/.claude/logs/agentfiles.jsonl` | Skill invocation log |
| `~/.claude/logs/sessions/session-*.jsonl` | Full tool-call traces per session |
| `~/.claude/logs/observations.md` | Pattern notes (append-only) |
| `~/.claude/logs/backlog.md` | Actionable improvements |
| `~/.claude/skills/hooks/skill-logger.py` | Hook that generates the logs |
| `af log` subcommands | CLI for querying/analyzing logs |
