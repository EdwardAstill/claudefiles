# zircote/.claude

**URL:** https://github.com/zircote/.claude
**Stars:** ~150 | **Type:** Personal dotfiles-style Claude Code configuration

## What It Is

A personal but comprehensive Claude Code configuration, closer in spirit to claudefiles than the larger public frameworks:
- 100+ named agents across 10 domain categories (language specialists, infrastructure, security, data/ML, fintech, blockchain, DevOps)
- 60+ reusable skills
- Custom slash commands for git and code review
- `includes/` folder with per-language coding standards (Python style, React conventions, testing standards)
- Optimized explicitly for Claude Opus

---

## What It Does Well

- **Deep agent taxonomy** — domain agents have defined tools, model preferences, and specialized context. Not just a system prompt; genuine specialization.
- **`includes/` for language standards** — coding standards, style guides, and testing conventions are separate files that skills reference and inject. Keeps skill files lean while delivering rich context when needed.
- **Non-engineering domain coverage** — business analysis, fintech, and blockchain agents appear alongside the standard dev specialists. Reflects a broader use case than most toolkits assume.
- **Per-agent model declarations** — each agent explicitly targets a model (mostly Opus). The intent is visible in config, not buried in prose.

---

## Weaknesses

- No installer, no manifest, no CLI — clone-and-manually-symlink
- No routing or discovery system — 100+ agents with no selection guidance
- Docs are thin; invocation mechanics and composition are undocumented
- Heavy coupling to Opus — may degrade on Sonnet/Haiku without adjustment
- No equivalent of `cf check` — no integrity verification

---

## What claudefiles Could Learn

| Idea | How to Apply |
|------|-------------|
| **`includes/` fragments** | Add a `claudefiles/includes/` folder for per-language standards (Python: ruff/pyright rules, TypeScript: biome config, etc.) that language-expert skills inject at invocation time — keeps skill prose focused on *when* to act, not *how* to format |
| **Model preference in manifest** | `manifest.toml` `model = "opus"` field per skill; `cf setup` or `cf agents` surfaces which skills want a heavier model — useful when choosing between Sonnet and Opus at session start |
| **Non-engineering domain agents** | Business analysis, writing, research-synthesis agents extend the toolkit beyond dev work |
