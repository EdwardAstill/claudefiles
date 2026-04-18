# anthropics/skills

**URL:** https://github.com/anthropics/skills
**Stars:** ~120k | **Forks:** ~13.9k | **License:** Apache-2.0 (most skills); source-available for document skills

## One-line

Anthropic's official, canonical reference implementation of the Agent Skills system — the repo the rest of the ecosystem forked, cloned, and imitated within months of launch.

## What it ships

- **17 top-level skills** under `skills/`, grouped informally into four categories:
  - *Creative & Design* — `algorithmic-art`, `canvas-design`, `theme-factory`, `slack-gif-creator`
  - *Development & Technical* — `mcp-builder`, `webapp-testing`, `web-artifacts-builder`, `frontend-design`, `claude-api`
  - *Enterprise & Communication* — `brand-guidelines`, `internal-comms`, `doc-coauthoring`
  - *Document Skills* (source-available, not Apache-2.0) — `docx`, `pdf`, `pptx`, `xlsx`
- **`skill-creator/`** — the meta-skill for authoring new skills; ships its own `agents/`, `assets/`, `eval-viewer/`, `references/`, and `scripts/` subtrees.
- **`spec/agent-skills-spec.md`** — the public Agent Skills specification (now hosted canonically at agentskills.io).
- **`template/`** — a minimal scaffold for new skills.
- **`.claude-plugin/`** — marketplace plugin manifest so the repo installs via `/plugin install document-skills@anthropic-agent-skills`.

## Notable patterns

- **Minimal frontmatter.** Only `name` and `description` are required. `description` is the primary routing signal and is written deliberately "pushy" — long, trigger-heavy, with explicit *do NOT use when* clauses (see `docx/SKILL.md`: ~15 trigger phrases plus negative scoping).
- **Progressive disclosure as architecture.** Metadata always in context (~100 words), SKILL.md body loaded on trigger, bundled `scripts/` / `references/` / `assets/` loaded only when referenced. Skill bodies aim for <500 lines; references >300 lines get their own TOC.
- **Bundled-resource convention.** Every non-trivial skill has the same three subfolders: `scripts/` (executable helpers), `references/` (long-form docs), `assets/` (templates, fonts, icons). This is structural, not decorative — scripts run, references are opened by path.
- **Theory-of-mind prose over rule lists.** The skill-creator explicitly coaches authors to explain *why* rather than pile up MUSTs and ALWAYSes.
- **No allowed-tools field.** Tool restriction is not part of the spec; skills operate inside Claude's ambient capability surface.
- **Per-skill LICENSE.txt.** Individual skills carry their own license file (the `docx` skill is proprietary even though the repo is Apache-2.0), signalling mixed-licensing is a first-class pattern.
- **Eval-viewer inside skill-creator.** Skills are built with an iterative loop: capture intent → interview → write → test with baseline → grade assertions → viewer → feedback → repeat.

## Compared to agentfiles

| Pattern | anthropics/skills | agentfiles | Verdict |
|---|---|---|---|
| Frontmatter | `name` + `description` only | name + description + tags + model hints in `manifest.toml` | agentfiles richer; Anthropic deliberately minimal |
| Bundled resources | `scripts/`, `references/`, `assets/` per skill | ad hoc; some skills inline, some reference | Adopt the trio convention |
| Progressive disclosure | Metadata / body / bundled — three tiers | Mostly single-tier SKILL.md | Steal this |
| Description style | Long, pushy, with negative triggers | Short, descriptive | Rewrite descriptions as triggers, not blurbs |
| Author loop | `skill-creator` + eval-viewer + assertion grading | `af` CLI + `af check` | Complementary; add eval-viewer analog |
| Licensing | Per-skill LICENSE.txt, mixed | Repo-wide | Fine as-is unless we ship proprietary skills |
| Distribution | Plugin marketplace (`/plugin install`) | Manual clone / symlink | Gap worth closing |

## Take-aways

1. **Adopt the `scripts/` + `references/` + `assets/` trio** as a required layout for any non-trivial agentfiles skill. Progressive disclosure falls out for free.
2. **Rewrite every `description` field as a trigger spec**, not a summary. Include negative triggers ("do NOT use when…"). This is the one change with the highest routing-quality payoff.
3. **Build an agentfiles analog of `skill-creator` + eval-viewer** — the loop (baseline test → assertion grading → viewer) is the backbone of how Anthropic iterates on skills, and we have nothing equivalent.
4. **Publish a `.claude-plugin/` manifest** so agentfiles installs via the marketplace, not via manual clone. Discoverability pays for itself.
5. **Keep `manifest.toml` richer than Anthropic's spec** — per-skill model hints and tags are genuine agentfiles value; don't regress to the minimum just because the canonical repo does.

**Last checked:** 2026-04-18
