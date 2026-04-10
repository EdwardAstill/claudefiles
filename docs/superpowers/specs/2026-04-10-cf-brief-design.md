# cf-brief — Design Spec

**Date:** 2026-04-10
**Status:** Approved for implementation

---

## Goal

A single `cf-brief` command that assembles one structured context snapshot by composing
the existing cf-* tools. Skills reference `cf-brief` instead of knowing about individual
`cf-context`, `cf-status`, `cf-versions`, and `cf-note` calls.

---

## Problem

Skills that need project context (task-analyser, superskill, manager) currently must know
about and call multiple individual tools. There is no single "give me everything relevant"
command. Adding a new cf-* tool requires updating every skill that assembles context.

---

## Design

### Output format

Markdown, consistent with all other cf-* tools. Four sections:

```
# PROJECT BRIEF
# Generated: YYYY-MM-DD HH:MM:SS

## Project
<name, root path, detected stack — from cf-context>

## Git State
<current branch, last 5 commits one-line, working tree status — inline git commands>

## Installed Skills
<skill names currently symlinked, one per line — from ls ~/.claude/skills/ and .claude/skills/>

## Notes
<contents of .claudefiles/notes.md if it exists, otherwise "(none)">
```

### Implementation approach

`bin/cf-brief` shells out to `cf-context` and reads `.claudefiles/notes.md`. It does NOT
shell out to `cf-status` because cf-status produces a full worktree topology (all branches,
all worktrees) — too verbose for a brief. Instead, cf-brief runs three targeted git commands
directly:

```bash
git branch --show-current                          # current branch
git log --oneline -5                               # last 5 commits
git status --short                                 # working tree summary
```

For installed skills: reads symlinks directly from `~/.claude/skills/` and `.claude/skills/`
(if it exists in the current project) using `ls`. Does not call `cf-agents` — that tool is
display-oriented and its output format is not stable for parsing.

Shells out to `cf-context` for the project identity section (stack detection logic lives
there; no duplication).

### Flags

- No flags: print to stdout
- `--write`: also write to `.claudefiles/brief.md`

Follows the exact pattern of `cf-context` and `cf-status`.

---

## Skill Integration

Three skills updated to add one instruction at the top of their context-gathering step:

> "Run `cf-brief` at task start and use its output as your project context."

Files to update:
- `dev-suite/management/orchestration/task-analyser/SKILL.md`
- `dev-suite/management/orchestration/superskill/SKILL.md`
- `dev-suite/management/orchestration/manager/SKILL.md`

Each currently references individual tools by name. Replace those references with a single
`cf-brief` call. Keep any references to cf-versions (dependency versions are not included
in cf-brief — out of scope to avoid bloat).

---

## Files

**Create:**
- `bin/cf-brief`

**Modify:**
- `manifest.toml` — add `cf-brief` to `[bin].install`
- `dev-suite/management/orchestration/task-analyser/SKILL.md`
- `dev-suite/management/orchestration/superskill/SKILL.md`
- `dev-suite/management/orchestration/manager/SKILL.md`

---

## What This Is Not

- Not a replacement for `cf-context` or `cf-status` — those remain for focused use
- Not a skill — it's a bin tool that skills invoke
- Not exhaustive — does not include dependency versions (use cf-versions separately)
