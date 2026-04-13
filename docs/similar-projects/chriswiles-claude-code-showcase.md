# ChrisWiles/claude-code-showcase

**URL:** https://github.com/ChrisWiles/claude-code-showcase
**Stars:** ~300 | **Type:** Reference implementation / integration showcase

## What It Is

A reference repo demonstrating how all pieces of Claude Code fit together in a real project:
- **Hooks + skills integration** — `UserPromptSubmit` hook reads skill frontmatter descriptions and auto-injects relevant skill context (essentially a hooks-layer skill router)
- **`PreToolUse` hooks** — blocks edits to main branch, enforces code review before merges
- **`PostToolUse` hooks** — auto-formats changed files, runs tests after edits
- **GitHub Actions integration** — scheduled maintenance jobs (monthly doc syncs, weekly quality reviews, dependency audits) treat Claude config as part of CI/CD
- **MCP bindings** — JIRA, Slack, and database MCPs wired in concretely

---

## What It Does Well

- **Hooks × skills integration** — the `UserPromptSubmit` hook that reads skill frontmatter and injects relevant skills is essentially a coarse automated router at the hook level. This is a hybrid approach: hooks do ambient routing; executor does fine-grained routing.
- **Treating config as CI** — running `af check` (or equivalent) as a GitHub Actions step, not just a local pre-commit tool, enforces manifest/REGION.md integrity on every PR.
- **Scheduled maintenance via Actions** — dependency audit on a weekly schedule, doc freshness review monthly. Maintenance that currently requires manual `af check` runs becomes automated.
- **Concrete MCP bindings** — shows exactly how to wire JIRA and Slack MCP servers into skills, not just that it's possible.

---

## Weaknesses

- Showcase repo — not distributable; no installer, no production hardening
- Advanced hook scripting is demonstrated but undocumented
- MCP bindings are tightly coupled to specific services (not generic patterns)
- No equivalent of `af agents` or `af check` — discovery is manual

---

## What agentfiles Could Learn

| Idea | How to Apply | Status |
|------|-------------|--------|
| **`UserPromptSubmit` hook as ambient router** | A hook that reads installed skill descriptions and injects a short "available skills" block into every prompt — coarse ambient awareness without a full skill invocation | open |
| **`af check` as a CI step** | Add `.github/workflows/check.yml` that runs `af check` on every PR to `agentfiles/` — catches REGION.md drift before it affects the manager | open |
| **Scheduled maintenance Actions** | A weekly workflow that verifies skill frontmatter is valid, manifest entries exist, and symlinks aren't broken | open |
| **`PostToolUse` auto-verification** | A hook that triggers `af check` after any edit to a `SKILL.md` or `REGION.md` — catch integrity violations at edit time, not commit time | open |
| **MCP integration patterns** | Document how to add an MCP server as a skill dependency in `manifest.toml` with concrete examples for common MCPs | open |
