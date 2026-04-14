# wshobson/commands

**URL:** https://github.com/wshobson/commands
**Stars:** ~200 | **Type:** Slash command collection

## What It Is

57 production-ready slash commands in a clean two-tier design:
- 15 **workflow** commands — multi-agent orchestration for complex tasks (`tdd-cycle`, `legacy-modernize`, `incident-response`)
- 42 **tool** commands — single-purpose atomic utilities

Commands can invoke one another, creating composable pipelines. Coverage spans AI/ML, testing, DevOps, security, data, debugging, and docs.

---

## What It Does Well

- **Two-tier naming** — the workflow/tool split maps directly to how you actually reach for a slash command. Workflows coordinate; tools execute.
- **Namespace prefixes** — `/workflows:feature-development`, `/tools:security-scan` keeps discoverability high even at 57 commands.
- **Full dev lifecycle coverage** — not just coding helpers; debugging, security, data, and docs all represented.
- **Inter-command invocation** — workflows call tool commands, producing genuine composition without a routing layer.

---

## Weaknesses

- No installer — manual file drop into `.claude/commands/`
- No manifest, no CLI, no dependency tracking
- No automated routing — user must always pick the right command
- No documented composition graph — not obvious which workflows call which tools

---

## What agentfiles Could Learn

| Idea | How to Apply |
|------|-------------|
| **Two-tier UI metaphor** | Consider surfacing the orchestrator/specialist split as a named concept in docs and `af agents` output |
| **Namespace prefixes in output** | `af agents --tree` could show `/orchestration:executor` vs `/coding:python-expert` style namespacing |
| **Composition documentation** | Document which skills call which (a "who-calls-who" graph) — currently implicit in skill descriptions only |
