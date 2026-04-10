# claudefiles Overhaul Design

**Date:** 2026-04-10  
**Status:** Approved

---

## Overview

Full overhaul of the claudefiles skill suite:

1. **Absorb superpowers** — copy all 14 superpowers skills into claudefiles; remove external dependency
2. **Restructure management** — split into `management/` (orchestration + meta) and `planning/` (new top-level category)
3. **Infrastructure fixes** — cf-setup robustness, registry sync enforcement, bootstrap pre-flight
4. **Language expert depth** — expand 4 language skills to match depth of git-expert/api-architect

---

## Section 1 — Repository Structure

### New top-level layout

```
dev-suite/
├── management/
│   ├── SKILL.md
│   ├── orchestration/
│   │   ├── simple-orchestrator/
│   │   ├── complex-orchestrator/
│   │   ├── dispatching-parallel-agents/    ← absorbed from superpowers
│   │   └── subagent-driven-development/    ← absorbed from superpowers
│   └── meta/
│       ├── skill-manager/                  ← renamed from agent-manager; moved from management/agent-manager/
│       └── writing-skills/                 ← absorbed from superpowers
│
├── planning/                               ← new top-level category
│   ├── SKILL.md
│   ├── brainstorming/                      ← absorbed from superpowers
│   ├── writing-plans/                      ← absorbed from superpowers
│   └── executing-plans/                    ← absorbed from superpowers
│
├── coding/
│   ├── SKILL.md
│   ├── api/api-architect/
│   ├── languages/
│   │   ├── SKILL.md
│   │   ├── python/                         ← skill name: python-expert
│   │   ├── typescript/                     ← skill name: typescript-expert
│   │   ├── rust/                           ← skill name: rust-expert
│   │   └── typst/                          ← skill name: typst-expert
│   ├── quality/
│   │   ├── SKILL.md
│   │   ├── tdd/                            ← absorbed from superpowers
│   │   ├── systematic-debugging/           ← absorbed from superpowers
│   │   ├── verification-before-completion/ ← absorbed from superpowers
│   │   ├── requesting-code-review/         ← absorbed from superpowers
│   │   ├── receiving-code-review/          ← absorbed from superpowers
│   │   └── simplify/                       ← absorbed from superpowers
│   └── version-control/
│       ├── git-expert/
│       ├── github-expert/
│       └── git-worktree-workflow/          ← merged: using-git-worktrees + finishing-a-development-branch
│
└── research/
    ├── SKILL.md
    ├── docs-agent/
    └── research-agent/
```

### Key structural decisions

- `planning/` is a new top-level category. The existing empty `dev-suite/management/planning/` directory is deleted; the new `dev-suite/planning/` is built fresh from absorbed superpowers skills.
- `agent-manager/` is relocated from `dev-suite/management/agent-manager/` to `dev-suite/management/meta/skill-manager/` and renamed to `skill-manager`.
- `management/` is now purely orchestration and meta tooling.
- `dispatching-parallel-agents` and `subagent-driven-development` live in `management/orchestration/` — they're execution patterns used by the orchestrators.
- `using-git-worktrees` and `finishing-a-development-branch` are merged into `git-worktree-workflow` (start + end of same lifecycle).
- `using-superpowers/` skill is excluded — redundant once absorbed.
- Directory names under `languages/` are short forms (`python/`, `typescript/` etc.); the `name:` field in each SKILL.md frontmatter retains the `-expert` suffix (`python-expert`, `typescript-expert`, `rust-expert`, `typst-expert`). No directories are renamed.

---

## Section 2 — Skill Absorption

### Skills to copy (14 total)

| Superpowers skill | Destination | Supporting files to include |
|---|---|---|
| `brainstorming` | `planning/brainstorming/` | visual-companion.md, spec-document-reviewer-prompt.md |
| `writing-plans` | `planning/writing-plans/` | plan-document-reviewer-prompt.md |
| `executing-plans` | `planning/executing-plans/` | — |
| `dispatching-parallel-agents` | `management/orchestration/dispatching-parallel-agents/` | — |
| `subagent-driven-development` | `management/orchestration/subagent-driven-development/` | implementer-prompt.md, code-quality-reviewer-prompt.md, spec-reviewer-prompt.md |
| `writing-skills` | `management/meta/writing-skills/` | testing-skills-with-subagents.md, anthropic-best-practices.md, persuasion-principles.md |
| `tdd` | `coding/quality/tdd/` | testing-anti-patterns.md |
| `systematic-debugging` | `coding/quality/systematic-debugging/` | root-cause-tracing.md, condition-based-waiting.md, defense-in-depth.md |
| `verification-before-completion` | `coding/quality/verification-before-completion/` | — |
| `requesting-code-review` | `coding/quality/requesting-code-review/` | code-reviewer.md |
| `receiving-code-review` | `coding/quality/receiving-code-review/` | — |
| `simplify` | `coding/quality/simplify/` | — |
| `using-git-worktrees` | `coding/version-control/git-worktree-workflow/` | merged with finishing-a-development-branch |
| `finishing-a-development-branch` | `coding/version-control/git-worktree-workflow/` | merged into single SKILL.md |

### Files excluded

- `test-pressure-*.md`, `test-academic.md`, `CREATION-LOG.md` — superpowers internal eval artifacts
- `using-superpowers/` — meta-skill for bootstrapping superpowers; irrelevant once absorbed
- `references/codex-tools.md`, `references/gemini-tools.md` — non-Claude platform adapters

### Cross-reference updates

All `superpowers:*` references in skill content must be updated to plain skill names. `writing-skills` and `simplify` are never referenced by name in other skill content and require no cross-reference updates.

| Old reference | New reference |
|---|---|
| `superpowers:brainstorming` | `brainstorming` |
| `superpowers:writing-plans` | `writing-plans` |
| `superpowers:executing-plans` | `executing-plans` |
| `superpowers:dispatching-parallel-agents` | `dispatching-parallel-agents` |
| `superpowers:subagent-driven-development` | `subagent-driven-development` |
| `superpowers:test-driven-development` | `tdd` |
| `superpowers:systematic-debugging` | `systematic-debugging` |
| `superpowers:verification-before-completion` | `verification-before-completion` |
| `superpowers:requesting-code-review` | `requesting-code-review` |
| `superpowers:receiving-code-review` | `receiving-code-review` |
| `superpowers:using-git-worktrees` | `git-worktree-workflow` |
| `superpowers:finishing-a-development-branch` | `git-worktree-workflow` |

---

## Section 3 — New and Updated Dispatcher Skills

### Dispatchers to create

**`planning/SKILL.md`** — new top-level dispatcher; routes to brainstorming / writing-plans / executing-plans by phase.

**`management/meta/SKILL.md`** — new subdirectory dispatcher; routes directly to `skill-manager` and `writing-skills` by name (does not sub-dispatch further).

### Dispatchers to update

**`management/SKILL.md`** — update to reflect new structure. Routes to `management/orchestration/` as a sub-dispatcher and to `management/meta/` as a sub-dispatcher. Planning is removed. The routing table at this level covers orchestration and meta only.

**`coding/quality/SKILL.md`** — update from placeholder to full routing table covering 6 leaf skills: tdd, systematic-debugging, verification-before-completion, requesting-code-review, receiving-code-review, simplify.

**`coding/version-control/`** — no dispatcher needed; git-expert/github-expert/git-worktree-workflow are self-describing.

### Mutually exclusive triggers (management + planning)

| Skill | Fires when |
|---|---|
| `simple-orchestrator` | Any new task — triage and route |
| `complex-orchestrator` | Escalated multi-skill task — plan the sequence |
| `brainstorming` | Have an idea, haven't designed it yet |
| `writing-plans` | Have an approved spec/design, need an implementation plan |
| `executing-plans` | Have a plan, want to hand off to a fresh parallel session |
| `subagent-driven-development` | Have a plan, executing in current session, tasks are sequential |
| `dispatching-parallel-agents` | Have independent tasks to run simultaneously right now |
| `skill-manager` | Want to see or manage installed skills |
| `writing-skills` | Creating or editing a skill |

---

## Section 4 — Infrastructure Fixes

### cf-setup: replace Python TOML parser

The current `bin/cf-setup` uses an inline Python block to parse `manifest.toml`. Replace with a pure awk pipeline. The rewrite is a **drop-in replacement**: same features, same output format, same `--write` behaviour writing to `.claudefiles/deps.md`. No scope reduction. The manifest format is already restricted to avoid awk edge cases.

### Registry sync: add cf-check

Add `bin/cf-check` — a script that:
1. Walks `dev-suite/` finding all `SKILL.md` files with a `name:` field
2. Checks each name exists in `dev-suite/registry.md` (**one-directional**: SKILL.md → registry only)
3. Reports missing entries as a plain list, one per line, using the same colour conventions as other cf-* tools
4. Exits non-zero if any entries are missing (makes it usable in pre-commit hooks or CI)

Add to `CLAUDE.md`: "Run `cf-check` before committing changes to dev-suite."

Also add `cf-check` to `manifest.toml` under `[bin]`.

### Bootstrap pre-flight checks

Add a pre-flight block at the top of `bootstrap.sh` that checks for `git`, `bash`, and `curl` and exits with a friendly message if any are missing.

### manifest.toml entries for new skills

Add entries for all 14 absorbed skills with their tool requirements.

---

## Section 5 — Language Expert Depth

Expand all 4 language skills to match the depth of `git-expert` and `api-architect`. Each skill should include:

- Toolchain setup and recommended versions
- LSP integration (how to invoke, what diagnostics to use)
- Common patterns with before/after examples
- Anti-patterns and when NOT to use a pattern
- Testing workflow (framework, runner, conventions)
- Package management (install, lock files, workspaces)
- Common mistakes + fixes

Directory names (`python/`, `typescript/`, `rust/`, `typst/`) are unchanged. The `name:` field in each SKILL.md frontmatter retains the `-expert` suffix.

---

## Section 6 — Registry and manifest.toml Updates

`dev-suite/registry.md` must be updated to include entries for all new skills with:
- Purpose
- Triggers
- Inputs / Outputs
- Tools Required
- Chains Into

`manifest.toml` must be updated with tool requirements for all new skills.

---

## Execution Order

1. **Skill absorption** — copy files, merge git-worktree-workflow, update cross-references; delete `management/planning/`; move and rename `agent-manager/` to `management/meta/skill-manager/`
2. **Dispatcher updates** — create `planning/SKILL.md` and `management/meta/SKILL.md`; update `management/SKILL.md` and `coding/quality/SKILL.md`
3. **Registry + manifest** — update both files with all new entries. Note: `cf-check` (added in step 4) is not expected to pass until this step is complete.
4. **Infrastructure** — cf-setup awk rewrite, cf-check script, bootstrap pre-flight, update CLAUDE.md
5. **Language expert depth** — expand 4 language skills

---

## Out of Scope

- Tests for bin tools (separate project)
- State persistence between sessions (intentional design)
- cf-agents performance optimisation (no real-world problem yet)
