# disler/claude-code-hooks-mastery

**URL:** https://github.com/disler/claude-code-hooks-mastery
**Stars:** ~5,800 | **Type:** Educational hooks deep-dive

## What It Is

A focused educational repo demonstrating Claude Code's complete hooks lifecycle. Implements all 13 hook types as standalone UV single-file Python scripts:

- **Hook types covered:** `PreToolUse`, `PostToolUse`, `UserPromptSubmit`, `SessionStart`, `SessionEnd`, `SubagentStart`, `SubagentStop`, and more
- **Patterns demonstrated:** exit-code semantics, security-blocking (blocking `rm -rf`, permission gating), context injection, audio TTS feedback, JSON audit logging
- Each hook is a self-contained UV script with embedded dependencies — no install step

---

## What It Does Well

- **Complete hook coverage** — every lifecycle event shown with a working example, not just the common ones
- **UV single-file scripts** — portable, zero-setup, embedded dependencies. A strong distribution primitive for helper scripts.
- **Security patterns** — blocking dangerous commands, permission gating on sensitive tools, and audit trails are production-grade patterns, not toy examples.
- **Audit trail via JSON logs** — logging every hook event to a structured file enables post-session analysis of what Claude did and why.
- **Exit-code semantics clearly documented** — the difference between exit 0 (allow), exit 1 (block with message), and exit 2 (block silently) is non-obvious; this repo makes it concrete.

---

## Weaknesses

- Purely educational — not designed to install as a reusable suite
- No graceful degradation if a hook script fails or the UV tool isn't installed
- No documentation on hook interaction order when multiple hooks fire on the same event
- No integration with a skill/command routing layer — hooks and skills are treated as separate systems
- No `settings.json` examples showing how to wire hooks into a real session config

---

## What claudefiles Could Learn

| Idea | How to Apply | Status |
|------|-------------|--------|
| **Add a hooks layer** | `PreToolUse` safety gate blocking dangerous Bash commands; `PostToolUse` skill logger. Install via `hooks/install-hooks.sh`. | **done** — `hooks/safety-gate.py`, `hooks/skill-logger.py` |
| **Security gates** | `PreToolUse` hook blocks `rm -rf`, `git push --force`, `DROP TABLE/DATABASE`, fork bomb, `dd if=`, `mkfs`. | **done** — `hooks/safety-gate.py` |
| **JSON audit log** | `PostToolUse` hook appends JSONL to `~/.claude/logs/claudefiles.jsonl` on every SKILL.md read; `cf log` views it. | **done** — `hooks/skill-logger.py` + `cf log` |
| **`SessionStart` hook replaces manual orientation** | A `SessionStart` hook that runs `cf context` and `cf status` automatically would replace the manual "executor orients at start" step | open |
| **UV single-file scripts in `scripts/`** | Skills with helper scripts could ship as UV single-file scripts — zero setup, portable, inline dependencies | open |
