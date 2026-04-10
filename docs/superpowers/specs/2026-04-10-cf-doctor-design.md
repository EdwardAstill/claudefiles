# cf-doctor — Design Spec

**Date:** 2026-04-10
**Status:** Approved for implementation

---

## Goal

A single `cf-doctor` command that checks the full health of a claudefiles installation
in one run. One command, full picture. Replaces ad-hoc debugging of "why isn't X working".

---

## Design

### Location resolution

Like all bin tools, uses `readlink -f "${BASH_SOURCE[0]}"` to resolve the script's real
path and derive the repo root (`SCRIPT_DIR/../`). All file lookups are relative to this.

### Checks (in order)

**1. Bin tools in PATH**

For each tool listed in `manifest.toml [bin].install`, check that the command exists in
PATH using `command -v`. Reports how many pass and lists any missing with the fix:
"Re-run `./install.sh --global` to reinstall bin tools."

**2. Global skills symlinked — valid symlinks**

Directly inspects `~/.claude/skills/` with `ls -la`. For each entry, verifies the symlink
target exists (not broken). Does not parse `cf-agents` output. Pass criterion: at least one
valid (non-broken) symlink exists. Reports broken symlinks by name.

**3. manifest.toml entries for installed skills**

For each `SKILL.md` in `dev-suite/` that is a leaf skill (no child SKILL.md files), checks
that `manifest.toml` has a `[skills.<name>]` entry. Same leaf-detection logic as `cf-check`.
Flags skills missing from manifest.

**4. REGION.md sync**

Calls `cf-check` internally (via subprocess). Pass: exit 0. Fail: surfaces cf-check output.

**5. MCP servers configured**

For each MCP server name declared in `manifest.toml` (lines matching `mcp = [...]`), checks
whether the server name appears in `~/.claude/settings.json` using `grep`. No jq required —
just looks for the string. This is a heuristic check, not a parse-and-validate check.
If `~/.claude/settings.json` doesn't exist, skips with a warning.

**6. `.claudefiles/` directory in current project**

Checks that `.claudefiles/` exists in the current git root. Skips (does not fail) when the
current directory IS the claudefiles repo itself (detected by checking for `dev-suite/` in
the repo root — avoids chronic false-positives during development). Reports as a warning
rather than a hard failure if missing elsewhere.

### Output format

```
cf-doctor — claudefiles health check

  ✓  Bin tools in PATH (13/13)
  ✓  Global skills — valid symlinks (30)
  ✗  manifest.toml entries — missing: memory-agent
  ✓  REGION.md sync (30 skills)
  ✓  MCP servers configured (context7)
  ⚠  .claudefiles/ directory — not found (run cf-init)

  1 error, 1 warning.
```

With `--verbose`: failing and warning checks expand to show exactly what's wrong and the
fix command. Passing checks also expand to list what was found.

**Exit codes:** 0 if no errors (warnings OK), 1 if any errors.

---

## Files

**Create:**
- `bin/cf-doctor`

**Modify:**
- `manifest.toml` — add `cf-doctor` to `[bin].install`
