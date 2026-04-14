# Helpful Projects

Comparative analysis of public Claude Code skill/plugin suites and related projects, grouped by their core architectural contribution.

## 🚀 Agent Platforms
*Managed runners and autonomous agents.*

| Project | Key Differentiator |
|---------|--------------------|
| [NousResearch/hermes-agent](agent-platforms/nousresearch-hermes-agent.md) | Self-improving AI agent with a "learning loop" for skill creation |
| [multica-ai/multica](agent-platforms/multica-ai.md) | Managed agents platform for team-based agent orchestration |
| [wshobson/agents](agent-platforms/wshobson-agents.md) | Mega library of 182+ agents and plugin-based orchestrators |
| [ruvnet/ruflo](agent-platforms/ruvnet-ruflo.md) | Enterprise-grade swarm orchestration with self-learning consensus |
| [Melty Labs: Conductor](agent-platforms/meltylabs-conductor.md) | Visual macOS dashboard for parallel agents in isolated worktrees |

## 📐 Methodology & Workflows
*Engines that enforce deterministic engineering processes.*

| Project | Key Differentiator |
|---------|--------------------|
| [obra/superpowers](methodology-and-workflows/obra-superpowers.md) | Enforced sequential dev methodology, cross-agent portability |
| [coleam00/Archon](methodology-and-workflows/coleam00-archon.md) | Deterministic, YAML-based AI coding workflows |
| [gsd-build/get-shit-done](methodology-and-workflows/gsd-build.md) | Advanced skill suite for phase-based project lifecycle management |
| [GitHub Next: Agentic Workflows](methodology-and-workflows/github-agentic-workflows.md) | Markdown-based automation for GitHub Actions and repo maintenance |
| [Spec Kit (GitHub)](methodology-and-workflows/github-spec-kit.md) | Structured workflow toolkit using `/specify`, `/plan`, and `/tasks` |

## 🛠️ Skill Suites
*Large collections of commands, experts, and personas.*

| Project | Key Differentiator |
|---------|--------------------|
| [alirezarezvani/claude-skills](skill-suites/alirezarezvani-claude-skills.md) | Mega library with 235+ production-ready skills across all domains |
| [Jeffallan/claude-skills](skill-suites/jeffallan-claude-skills.md) | Workflow-optimized skills with automatic "trigger chains" |
| [nylas/skills](skill-suites/nylas-skills.md) | Specialized skill pack for Email, Calendar, and Contacts APIs |
| [qdhenry/Claude-Command-Suite](skill-suites/qdhenry-claude-command-suite.md) | Mega collection of 216+ commands and external integrations |
| [SuperClaude-Org/SuperClaude_Framework](skill-suites/superclaude-framework.md) | Behavioral modes and agent personas with model preferences |
| [wshobson/commands](skill-suites/wshobson-commands.md) | Clean two-tier workflow/tool split with namespace prefixes |
| [zircote/.claude](skill-suites/zircote-claude.md) | `includes/` fragments for standards, 100+ deep domain agents |

## 📚 Education & Showcases
*Guides, hooks deep-dives, and implementation examples.*

| Project | Key Differentiator |
|---------|--------------------|
| [disler/claude-code-hooks-mastery](education-and-showcases/disler-hooks-mastery.md) | All 13 hook types, UV scripts, and security gate patterns |
| [ChrisWiles/claude-code-showcase](education-and-showcases/chriswiles-claude-code-showcase.md) | Hooks × skills integration and skill integrity CI |
| [johnlindquist/claude-hooks](education-and-showcases/johnlindquist-claude-hooks.md) | TypeScript-based framework for typed, programmatic lifecycle hooks |

---

## Cross-Cutting Themes

### What agentfiles has that comparable projects don't

- Two-step installer: `install.sh` (bootstrap) + `af install` (full install with scoped/granular control)
- A CLI tool (`af`) with context gathering, integrity checking, and agent inventory
- Explicit routing/executor layer — user never has to pick a skill manually
- `manifest.toml` tracking tool requirements and category per skill
- Category-level dispatchers and `REGION.md` for manager planning
- **Hooks layer** — `PreToolUse` safety gate blocking dangerous Bash commands; `PostToolUse` skill logger

### What comparable projects do that agentfiles currently doesn't

| Gap | Best Reference | Priority | Status |
|-----|----------------|----------|--------|
| **`SessionStart` hook** — auto-run `af context` + `af status` | hooks-mastery | High | open |
| **`includes/` fragments** — per-language standards injected at invocation time | zircote | Medium | open |
| **Behavioral modes** — operating posture switches (token-efficiency, deep-research) | SuperClaude | Medium | open |
| **Skill Learning Loop** — agent records new successful patterns | hermes-agent | Low | open |
| **Typed Hook Payloads** — auto-completion and typed JSON for hook dev | johnlindquist | Low | open |
| **Workflow Trigger Chains** — skills explicitly referencing the "next" specialist | Jeffallan | Low | open |
