# cf-doctor — Design Spec

**Date:** 2026-04-10
**Status:** Approved for implementation

**Depends on:** Tool management migration (bin/ → tools/python/)

---

## Goal

A single `cf doctor` command that checks the full health of a claudefiles installation.
One command, full picture.

---

## Design

### Implementation

New Python module: `tools/python/src/cf/doctor.py`

Registered in `main.py`:
```python
from cf import doctor
app.add_typer(doctor.app, name="doctor")
```

Entry in `tools/tools.json`:
```json
{
  "name": "doctor",
  "type": "internal",
  "package": "cf",
  "description": "Check the health of this claudefiles installation",
  "usage": "cf doctor [--verbose]"
}
```

### Path resolution

Uses `importlib.resources` or `__file__` to locate the repo root — the same approach
as other `cf` modules via shared `cf/lib.py`.

### Checks (in order)

**1. `cf` subcommands available**

Imports `cf.main` and checks that all expected sub-apps are registered. Pass: all
subcommands present. Fail: lists missing subcommands.

**2. Global skills symlinked — valid symlinks**

Inspects `~/.claude/skills/` directly. For each entry, checks the symlink target
exists (not broken). Reports broken symlinks by name. Pass criterion: at least one
valid symlink.

**3. manifest.toml entries for installed skills**

For each leaf `SKILL.md` in `skills/` (no child SKILL.md files), checks that
`manifest.toml` has a `[skills.<name>]` entry. Flags any skill missing from manifest.

**4. REGION.md sync**

Calls `cf check` internally. Pass: exit 0. Fail: surfaces `cf check` output.

**5. MCP servers configured**

For each MCP server name declared in `manifest.toml [skills.*].mcp` fields, checks
whether the name appears in `~/.claude/settings.json` via string search. Skips with
a warning if `~/.claude/settings.json` doesn't exist.

**6. `.claudefiles/` directory in current project**

Checks that `.claudefiles/` exists in the current git root. Skips (no failure) when
the current directory IS the claudefiles repo itself — detected by presence of
`skills/` in the repo root, to avoid chronic false-positives during development.
Reports as a warning (not error) if missing elsewhere.

### Output format

```
cf doctor — claudefiles health check

  ✓  cf subcommands (12/12)
  ✓  Global skills — valid symlinks (30)
  ✗  manifest.toml entries — missing: memory-agent
  ✓  REGION.md sync (30 skills)
  ✓  MCP servers configured (context7)
  ⚠  .claudefiles/ directory — not found (run cf init)

  1 error, 1 warning.
```

`--verbose`: expands all checks (passing and failing) to show full details and fix
commands.

**Exit codes:** 0 if no errors (warnings OK), 1 if any errors.

---

## Files

**Create:**
- `tools/python/src/cf/doctor.py`

**Modify:**
- `tools/python/src/cf/main.py` — register doctor sub-app
- `tools/tools.json` — add doctor entry
