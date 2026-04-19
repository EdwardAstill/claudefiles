# anthropics/skills

**URL:** https://github.com/anthropics/skills
**Stars:** ~120,000 | **Type:** Upstream skill specification + reference library

## What It Is

The official Anthropic Agent Skills repository — both the formal spec and a reference library of skills that ship across Claude.ai, the Skills API, and Claude Code. Defines the convention agentfiles' own `SKILL.md` format derives from.

- **`./spec/`** — the Agent Skills specification: required frontmatter (`name`, `description`), file layout, discovery rules
- **`./template/`** — minimal scaffold for authoring a new skill
- **`./skills/`** — reference implementations across creative/design, dev/technical, enterprise/comms, and document-handling (DOCX/PDF/PPTX/XLSX)
- **`.claude-plugin/`** — Claude Code plugin metadata so the whole repo can be installed as one
- Cross-platform: same skill files work in Claude.ai (paid), the Skills API, and Claude Code via plugin install

---

## What It Does Well

- **Spec is short and frozen-ish** — the SKILL.md frontmatter contract is small enough to memorize and stable enough to build tooling against (which is what agentfiles' `af audit` checks do)
- **Document skills are production-grade** — the DOCX/PDF/PPTX/XLSX skills are the same ones backing Claude.ai's document features; not toys
- **Single source of truth across surfaces** — same skill format works in three product contexts, which validates the convention's portability
- **Plugin packaging shown end-to-end** — `.claude-plugin/` directory demonstrates how a skill collection becomes a one-command install

---

## Weaknesses

- **No trigger-spec convention** — descriptions are free-form prose, not the structured "Use when X. Don't use when Y." pattern agentfiles enforces
- **No regional grouping or routing layer** — flat skill list; no equivalent of agentfiles' REGION.md / manager-router architecture
- **Spec is descriptive, not prescriptive about scale** — no guidance on what to do once you have 50+ skills (which is exactly the problem agentfiles solves)

---

## Take

The authoritative upstream reference — agentfiles' `SKILL.md` schema must remain compatible with this spec or it stops working with the Claude Code plugin loader. Worth periodically re-reading `./spec/` to catch frontmatter additions. The reference skills themselves are mostly orthogonal to agentfiles (different domains), but the **document skills** are a useful template for any future "produce a polished artifact" skill in agentfiles that needs to go beyond markdown.
