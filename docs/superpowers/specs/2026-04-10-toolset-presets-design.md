# Toolset Presets — Design Spec

**Date:** 2026-04-10
**Status:** Approved for implementation

---

## Goal

Named skill bundles declared in `manifest.toml` and installed via a `cf-presets` bin
tool. User says "set up for a Rust CLI project" → deterministic install of the right
skills, no per-item reasoning needed. Skill-manager references `cf-presets` instead of
a hardcoded selection table.

---

## Design

### manifest.toml format

New `[presets.*]` sections. All `skills` arrays stay on a single line — required by the
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

### cf-presets tool

```
cf-presets list              # show all presets with descriptions and skill lists
cf-presets install <name>    # install preset into current project (--local)
cf-presets install <name> --global   # install globally
```

`list` with an optional preset name (`cf-presets list rust-cli`) filters to one preset.
No separate `show` subcommand — list handles both cases.

**`cf-presets list` output:**
```
Available presets:

  python-api       Python API or service project
                   python-expert, tdd, api-architect, git-expert

  rust-cli         Rust CLI or systems project
                   rust-expert, tdd, systematic-debugging, git-expert
  ...
```

**`cf-presets install <name>`** loops through the preset's skill list and calls
`install.sh --local --skill <name>` for each. Detects already-installed skills by
checking for a symlink at `.claude/skills/<name>` — if the symlink exists, skips with
"already installed" note. Reports installed vs skipped counts at end.

### cf-presets requires a full global install

`cf-presets` is a bin tool declared in `[bin].install`. Per CLAUDE.md, bin tools are
only symlinked on `--global` full dev-suite installs (no `--skill`/`--category` flags).
Skill-manager should note this: if `cf-presets` is not on PATH, fall back to calling
`install.sh --local --skill <name>` directly for each skill.

### skill-manager SKILL.md update

Replace the hardcoded `Signal → Install` table with the `cf-presets` workflow:

1. After user describes project, run `cf-presets list` and show output
2. Ask: "Which preset fits your project, or should I build a custom set?"
3. If a preset: `cf-presets install <name>`
4. If custom: fall back to the existing per-signal selection logic (keep that section,
   just demote it to a fallback for "no preset fits")

---

## Files

**Create:**
- `bin/cf-presets`

**Modify:**
- `manifest.toml` — add `[presets.*]` sections, add `cf-presets` to `[bin].install`
- `dev-suite/management/meta/skill-manager/SKILL.md` — update /setup workflow
