# Toolset Presets — Design Spec

**Date:** 2026-04-10
**Status:** Approved for implementation

**Depends on:** Tool management migration (bin/ → tools/python/)

---

## Goal

Named skill bundles declared in `manifest.toml` and installed via `cf presets`. User
says "set up for a Rust CLI project" → deterministic install of the right skills.
Skill-manager references `cf presets` instead of a hardcoded selection table.

---

## Design

### manifest.toml format

New `[presets.*]` sections. All `skills` arrays on a single line — required by the
awk/grep parser (CLAUDE.md: "avoid unusual formatting — multi-line arrays").

```toml
[presets.python-api]
skills = ["python-expert", "tdd", "api-architect", "git-expert"]
description = "Python API or service project"

[presets.rust-cli]
skills = ["rust-expert", "tdd", "systematic-debugging", "git-expert"]
description = "Rust CLI or systems project"

[presets.typescript-web]
skills = ["typescript-expert", "tdd", "api-architect", "git-expert"]
description = "TypeScript web app, API, or Node service"

[presets.docs-site]
skills = ["typst-expert", "docs-agent"]
description = "Documentation, papers, or typeset documents"

[presets.research]
skills = ["research-agent", "docs-agent"]
description = "Research, evaluation, or exploration work"

[presets.full]
skills = ["python-expert", "rust-expert", "typescript-expert", "typst-expert", "tdd", "systematic-debugging", "api-architect", "git-expert", "github-expert", "git-worktree-workflow", "docs-agent", "research-agent"]
description = "Everything — install all skills"
```

Presets are additive. Installing two presets installs the union.

### Implementation

New Python module: `tools/python/src/cf/presets.py`

Registered in `main.py`:
```python
from cf import presets
app.add_typer(presets.app, name="presets")
```

Entry in `tools/tools.json`:
```json
{
  "name": "presets",
  "type": "internal",
  "package": "cf",
  "description": "Install named skill bundles for common project types",
  "usage": "cf presets list [<name>] | cf presets install <name> [--global]"
}
```

### CLI interface

```
cf presets list               # show all presets with descriptions and skill lists
cf presets list rust-cli      # filter to one preset
cf presets install <name>     # install into current project (--local)
cf presets install <name> --global   # install globally
```

**`cf presets list` output:**
```
Available presets:

  python-api       Python API or service project
                   python-expert, tdd, api-architect, git-expert

  rust-cli         Rust CLI or systems project
                   rust-expert, tdd, systematic-debugging, git-expert
  ...
```

**`cf presets install <name>`:**
- Reads `[presets.<name>]` from `manifest.toml`
- For each skill: checks for symlink at `.claude/skills/<name>` to detect already-installed
- Calls `cf install --local --skill <name>` for each not-yet-installed skill
- Reports installed vs already-present counts at end

Presets require the `cf` tool to be installed (via `bootstrap.sh` or `uv tool install`).
If `cf` is not available, skill-manager falls back to calling `cf install --local --skill`
directly for each skill.

### skill-manager SKILL.md update

Replace the hardcoded `Signal → Install` table with the `cf presets` workflow:

1. After user describes project, run `cf presets list` and show output
2. Ask: "Which preset fits, or should I build a custom set?"
3. If preset: `cf presets install <name>`
4. If custom: fall back to existing per-signal selection logic (kept as fallback section)

---

## Files

**Create:**
- `tools/python/src/cf/presets.py`

**Modify:**
- `tools/python/src/cf/main.py` — register presets sub-app
- `tools/tools.json` — add presets entry
- `manifest.toml` — add `[presets.*]` sections
- `skills/management/meta/skill-manager/SKILL.md` — update /setup workflow
