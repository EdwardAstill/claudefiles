# obra/superpowers

**URL:** https://github.com/obra/superpowers
**Stars:** ~147,000 | **Type:** Agentic skills framework & software development methodology

## What It Is

The highest-starred Claude Code skills project by a large margin. A lean, opinionated collection of 14 skills that enforce a structured development methodology across multiple AI coding agents:

- **14 skills** covering the full dev loop: brainstorming → planning → execution → code review → testing → completion
- **Multi-platform** — targets Claude Code, Cursor, Codex, OpenCode, GitHub Copilot CLI, and Gemini CLI via separate plugin dirs (`.claude-plugin/`, `.cursor-plugin/`, `.codex/`, `.opencode/`)
- **Mandatory workflows, not suggestions** — the CLAUDE.md instructs the agent to check for relevant skills before any task, making them automatic rather than opt-in
- Skills overlap significantly with claudefiles' own skills (brainstorming, systematic-debugging, test-driven-development, subagent-driven-development, writing-plans, using-git-worktrees)

**Skills list:**
brainstorming, dispatching-parallel-agents, executing-plans, finishing-a-development-branch, receiving-code-review, requesting-code-review, subagent-driven-development, systematic-debugging, test-driven-development, using-git-worktrees, using-superpowers, verification-before-completion, writing-plans, writing-skills

---

## What It Does Well

- **Enforced sequential methodology** — the README is explicit: design → workspace → plan → implement with review → test → finish. The agent can't skip stages.
- **Cross-agent portability** — same skill set runs on 6+ AI coding agents without modification. The multi-platform install is real infrastructure, not an afterthought.
- **Extreme reach** — 147k stars suggests it has become a de facto standard for structured AI-assisted development. The skill vocabulary (brainstorming, writing-plans, executing-plans) has likely shaped the broader ecosystem.
- **Minimal surface area** — 14 skills, no routing layer, no manifest, no CLI. Easier to fork and adapt than heavier frameworks.
- **TDD-first** — test-driven-development is a first-class required step, enforcing red/green/refactor discipline rather than treating tests as optional.

---

## Weaknesses

- **No routing/executor** — user (or CLAUDE.md injection) must identify the right skill. No equivalent of claudefiles' `executor` auto-routing.
- **No CLI** — no `cf`-style tool for context gathering, integrity checking, or skill inventory.
- **No category hierarchy** — flat skill list; as the collection grows, discovery and maintenance will be harder.
- **No manifest** — no declared tool requirements or MCP dependencies per skill.
- **No install scoping** — no `--global` / `--local` distinction; install is platform-specific manual setup.
- **No REGION.md / manager planning** — no machine-readable skill catalog for orchestrators to use during planning.
- **Skills overlap with claudefiles exactly** — brainstorming, systematic-debugging, tdd, subagent-driven-development, writing-plans, verification-before-completion are direct equivalents. Not a weakness per se, but confirms claudefiles' approach is on the right track.

---

## What claudefiles Could Learn

| Idea | How to Apply |
|------|-------------|
| **Multi-platform plugin dirs** | Add `.cursor-plugin/` and `.codex/` alongside `.claude-plugin/` — each pointing at the same skills with agent-specific CLAUDE.md wrappers |
| **Enforced sequential stages** | `executor` already routes to brainstorming and writing-plans, but could be more explicit about *blocking* later stages until earlier ones are complete |
| **`using-superpowers` meta-skill pattern** | claudefiles has `using-claudefiles` but it could be more prominent as the session-start orientation skill |
| **`finishing-a-development-branch` skill** | A dedicated "done checklist" skill (tests passing, REGION.md updated, `cf check` clean, PR drafted) that executor calls at the end of feature work |
