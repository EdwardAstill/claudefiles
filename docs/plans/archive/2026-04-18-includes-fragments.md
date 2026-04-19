# Includes Fragments System

**Status:** partially implemented (2026-04-18)
**Inspired by:** `zircote/.claude` — see `research/projects/skill-suites/zircote-claude.md`

## Status (2026-04-18)

### Done

- Loader module `tools/python/src/af/includes.py` with `expand()`,
  `read_fragment()`, `list_fragments()`, `missing_includes()`.
- CLI surface wired under `af include`:
  - `af include list` — list every fragment under `agentfiles/includes/`.
  - `af include show <slug>` — print a fragment body with frontmatter stripped.
  - `af include expand <path>` — print SKILL.md with fragments inlined under
    a `## Shared Conventions` block.
  - `af include check <path>` — verify every `includes:` entry resolves.
- 12 unit tests in `tools/python/tests/test_includes.py` covering the loader,
  missing-include detection, and the four CLI subcommands. `pytest` green
  (128 passed, 1 skipped).
- Five concrete fragments shipped (75–100 lines each, tooling-focused rather
  than the purely language-agnostic set originally sketched in §3):
  - `agentfiles/includes/python/pyright.md`
  - `agentfiles/includes/python/ruff.md`
  - `agentfiles/includes/python/uv.md`
  - `agentfiles/includes/typescript/tsc-strict.md`
  - `agentfiles/includes/rust/clippy.md`
- `agentfiles/coding/languages/python/SKILL.md` (python-expert) migrated to
  use `includes: [python/pyright, python/uv, python/ruff]`. Line count
  dropped from 159 → 121 in the SKILL.md body; fragment content lives once
  in `includes/` instead.
- `af check` still passes, `af audit` regression-free (same 34 pre-existing
  issues, same 4/8 summary), `af ak list` unchanged.
- Second-wave migration landed 2026-04-19:
  - `agentfiles/coding/languages/rust/SKILL.md` uses
    `includes: [rust/clippy]`. Clippy toolchain row + "Ignoring clippy
    warnings" anti-pattern/common-mistake entries removed from the body;
    net line count 189 → 193 because the frontmatter block + restyled
    "Toolchain at a glance" table cost a few lines over what the inline
    clippy rows did (the bulk of the clippy content — 81 lines — now
    lives once in `includes/rust/clippy.md`).
  - `agentfiles/coding/languages/typescript/SKILL.md` uses
    `includes: [typescript/tsc-strict]`. Strict-mode config block,
    forbidden-escape-hatch table, and type-only-import section removed
    from the body (now in the fragment). 181 → 169 lines.
  - `agentfiles/coding/languages/typst/SKILL.md` uses
    `includes: [typst/tinymist]`. New fragment
    `agentfiles/includes/typst/tinymist.md` (92 lines) shipped alongside
    the migration — covers LSP verbs, install, `tinymist.toml` config,
    and diagnostics interpretation. Skill body 162 → 153 lines.
  - `af include check` resolves on all three files; `af include expand`
    produces coherent `## Shared Conventions` sections. pytest suite
    still 128 passed / 1 skipped, `af audit` 8/8 passed.

### Remaining

- `ui-expert` / `tui-expert` were read in the second-wave pass and
  deliberately left as-is — these are design-spec skills, not language
  toolchain skills. Their content (design intelligence, framework widget
  catalogs, component-spec template, TUI color/keyboard design) is
  genuinely unique per skill; no shared tooling fragment fits without
  fabricating duplication. The original `handoff/to-language-expert`
  fragment proposed in §3 is still viable if the handoff paragraphs
  across `ui`, `tui`, and any future design experts converge — revisit
  then.
- Extract the language-agnostic fragments originally proposed in §3
  (`lsp/base-workflow`, `docs/fetching`, `testing/structure`,
  `packaging/lockfile`, `handoff/to-language-expert`,
  `outputs/expert-footer`). These were deferred in favour of the
  tooling-specific fragments the task brief pinned. Revisit once two more
  language experts are migrated — the shape of shared content will be
  clearer.
- Route the Claude-side skill-invocation code path through `expand()` so
  the model sees the assembled body rather than the raw SKILL.md. Today
  the loader runs on demand; inline auto-expansion is a follow-up.
- Wire `af check` to call `missing_includes()` on every SKILL.md so broken
  references fail the existing pre-commit/CI command. (Per-skill check
  already exists via `af include check`.)
- `manifest.toml` untouched. An `[includes.*]` registry is still optional;
  decide once the second-wave migration tells us whether fragments need
  declared owners / tool tags.
- `AGENTS.md` / `README.md` paragraph linking this plan (step 8 in §6) —
  still TODO.

## 1. Goal

Centralize shared skill conventions (LSP workflow, doc fetching, testing, packaging) in `agentfiles/includes/` so language-expert skills reference them instead of re-authoring.

## 2. Current state

Four duplicated blocks across the language experts:

- **LSP preamble** — `skills/python-expert/SKILL.md:17-27`, `skills/rust-expert/SKILL.md:17-30`, `skills/typescript-expert/SKILL.md:17-30`, `skills/typst-expert/SKILL.md:16-27`.
- **Documentation fetching** (context7 → WebFetch → `af versions --write`) — `python:33-39`, `rust:33-39`, `typescript:33-37`, `typst:29-40`.
- **Testing structure** (unit/integration split, fixtures, run commands) — `python:82-119`, `rust:108-145`, `typescript:95-136`.
- **Outputs footer** — `python:156-159`, `rust:185-189`, `typescript:177-181`, `typst:158-162`.

The `ui-expert` → language-expert handoff (`skills/ui-expert/SKILL.md:756-775`) and `tui-expert` equivalent (`skills/tui-expert/SKILL.md:246-296`) are also duplicates. One convention change today means four-plus edits plus drift hunt.

## 3. Target state

```
agentfiles/includes/
  lsp/base-workflow.md         # "diagnostics first" + four standard LSP verbs
  docs/fetching.md             # context7 → WebFetch → af versions order
  testing/structure.md         # unit/integration split shape
  packaging/lockfile.md        # commit-lockfile, frozen-lockfile in CI
  handoff/to-language-expert.md # ui/tui → *-expert contract
  outputs/expert-footer.md     # "linter-clean, LSP diagnostics report"
```

Each fragment: Markdown, 30–80 lines, no frontmatter, language-agnostic. Language-specific commands (`ruff` vs `clippy`) stay inline in SKILL.md.

## 4. Include syntax

**Frontmatter `includes:` list.**

```yaml
---
name: python-expert
description: >
  ...
includes:
  - lsp/base-workflow
  - docs/fetching
  - testing/structure
  - outputs/expert-footer
---
```

Reasoning: frontmatter is already parsed by `af check` — no new parser. Declarative, so `grep -r "includes:"` answers "who uses fragment X?" Inline `@include(...)` hides deps from tooling; a session-start hook adds runtime magic for no gain.

## 5. Loading semantics

**Inline expansion at skill-invocation time**, via a preprocessor — not the model.

`Skill("python-expert")` triggers `tools/python/src/af/includes.py::expand(path)`. It reads the SKILL.md, pulls each entry from `agentfiles/includes/<path>.md`, and appends them under a `## Shared Conventions` block. Expanded text is what Claude sees.

Rejected: **session-start injection** preloads fragments for skills the user never invokes — wastes context. **Lazy-on-reference** adds a tool round-trip per fragment. Trade-off accepted: fragment edits apply on the *next* invocation, matching current SKILL.md behaviour.

## 6. Migration plan

1. Add `tools/python/src/af/includes.py` with `expand(path) -> str` + tests. Wire into `af check` first (read-only: fail if an `includes:` entry has no matching file).
2. Route the skill-invocation code path through `expand()`. Behaviour identical when `includes:` is absent.
3. Extract `lsp/base-workflow.md` verbatim from `python-expert/SKILL.md:17-27`, update frontmatter, diff expanded output against pre-change file (must match modulo whitespace). Repeat for rust, typescript, typst.
4. Repeat for `docs/fetching` and `outputs/expert-footer` across the same four skills.
5. Extract `testing/structure` and `packaging/lockfile` — shared shape only, language commands stay inline.
6. Extract `handoff/to-language-expert`; update `ui-expert` and `tui-expert`.
7. Add `af skills includes <name>` helper: lists fragments a skill references.
8. One-paragraph note in `AGENTS.md` and `README.md` linking this plan.

## 7. Scope limits — NOT an include

- Ephemeral notes / lessons learned — belong in `docs/wiki/`.
- Per-project conventions — belong in `CLAUDE.md`.
- Per-task details — belong in the prompt.
- Anything used by exactly one skill (not shared → inline).
- Skill-selection or routing logic (lives in `using-agentfiles`).
- Long narrative prose. Hard cap: 100 lines per fragment.

## 8. Risks and open questions

- **Context bloat.** Inline expansion grows skill size. Mitigation: 100-line cap + `af check --size` warning.
- **Heading conflicts.** If SKILL.md and a fragment both have `## Testing`, which wins? Proposal: fragments land under a terminal `## Shared Conventions` block; SKILL.md body wins for duplicate headings. Revisit on first real conflict.
- **Drift across forks.** Downstream consumers pinning old versions miss fragment updates silently. Mitigation: `# version:` comment at top of each fragment, surfaced by `af check`.
- **Open:** fragments including other fragments? Default no — revisit only on real duplication inside the fragment set.
- **Open:** lint rule rejecting new inline LSP/testing blocks in SKILL.md after migration step 4? Probably yes, as follow-up.
