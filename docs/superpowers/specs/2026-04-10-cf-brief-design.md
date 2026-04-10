# cf-brief — Design Spec

**Date:** 2026-04-10
**Status:** Approved for implementation

**Depends on:** Tool management migration (dev-suite/ → skills/, bin/ → tools/python/)

---

## Goal

A single `cf brief` command that assembles one structured context snapshot. Skills
reference `cf brief` instead of knowing about individual `cf context`, `cf status`, and
`cf note` calls.

---

## Design

### Implementation

New Python module: `tools/python/src/cf/brief.py`

Registered in `main.py`:
```python
from cf import brief
app.add_typer(brief.app, name="brief")
```

Entry in `tools/tools.json`:
```json
{
  "name": "brief",
  "type": "internal",
  "package": "cf",
  "description": "Assemble a project context snapshot — git state, installed skills, and notes",
  "usage": "cf brief [--write]"
}
```

### Output format

Markdown, consistent with `cf context` and `cf status`. Four sections:

```
# PROJECT BRIEF
# Generated: YYYY-MM-DD HH:MM:SS

## Project
<name, root path, detected stack — from cf context logic>

## Git State
<current branch, last 5 commits one-line, working tree status summary>

## Installed Skills
<skill names symlinked in ~/.claude/skills/ and .claude/skills/, one per line>

## Notes
<contents of .claudefiles/notes.md if it exists, otherwise "(none)">
```

### Implementation notes

- Reuses logic from `cf/context.py` for project identity (no duplication)
- Runs three targeted git commands inline for git state: `git branch --show-current`,
  `git log --oneline -5`, `git status --short`
- Reads symlinks directly from `~/.claude/skills/` and `.claude/skills/` (if present) —
  does not call `cf agents`
- Reads `.claudefiles/notes.md` if present
- Does not include dependency versions (`cf versions` remains a separate call)

### Flags

- `--write`: also write to `.claudefiles/brief.md`

---

## Skill Integration

Three skills updated to add one instruction at the top of their context-gathering step:

> "Run `cf brief` at task start and use its output as your project context."

Files to update (post-migration paths):
- `skills/management/orchestration/task-analyser/SKILL.md`
- `skills/management/orchestration/superskill/SKILL.md`
- `skills/management/orchestration/manager/SKILL.md`

Each currently references individual tools by name. Replace those references with a single
`cf brief` call. Keep any references to `cf versions` — dependency versions are out of
scope for the brief.

---

## Files

**Create:**
- `tools/python/src/cf/brief.py`

**Modify:**
- `tools/python/src/cf/main.py` — register brief sub-app
- `tools/tools.json` — add brief entry
- `skills/management/orchestration/task-analyser/SKILL.md`
- `skills/management/orchestration/superskill/SKILL.md`
- `skills/management/orchestration/manager/SKILL.md`
