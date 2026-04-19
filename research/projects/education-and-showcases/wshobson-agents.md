# wshobson/agents

**URL:** https://github.com/wshobson/agents
**Stars:** ~33,900 | **Type:** Production-scale multi-agent suite + orchestration framework

## What It Is

A maximalist Claude Code agent library — the largest curated suite in the ecosystem. Organized for installability, not just browsing:

- **184 specialized agents** spanning architecture, security, infrastructure, data/AI, and domain verticals
- **78 single-purpose plugins** designed to load minimal context per install
- **150 agent skills** following progressive disclosure (load metadata first, expand on demand)
- **98 commands** for scaffolding, testing, security scanning, infra setup
- **16 multi-agent orchestrators** coordinating workflows like full-stack feature dev, security hardening, ML pipeline execution, incident response
- **Three-tier model strategy** — Opus 4.7 / Sonnet 4.6 / Haiku 4.5 assigned per task class for cost/latency tuning

---

## What It Does Well

- **"Install only what you need"** — plugin granularity is the explicit design goal; loading the security plugin doesn't drag in the ML-ops plugin's 30 agents
- **Tiered model assignment as a first-class concept** — most repos hardcode one model; this one treats model selection as a per-agent configuration knob
- **Orchestrator catalog** — 16 named workflows is enough to study patterns (when do you spawn parallel agents? when do you serialize? when do you hand off?)
- **Production-realistic scope** — incident response, security hardening, ML pipelines are real enterprise workflows, not toy CRUD apps

---

## Weaknesses

- **Sheer size is a discovery problem** — 184 agents × 150 skills × 98 commands is hard to navigate without the plugin filter; the install-only-what-you-need pattern is necessary precisely because it's overwhelming
- **No regional / hierarchical routing** — relies on plugin scoping for context budgeting rather than a manager/router layer
- **Heavy on quantity, lighter on per-agent quality docs** — individual agents vary; some are thin
- **Opinionated three-tier model strategy** assumes API access to all three tiers, which is an enterprise assumption

---

## Take

The most useful repo to study if agentfiles ever needs to scale past ~100 skills. The **plugin-as-context-budget** pattern (load only the plugin you need) is a different solution to the same problem agentfiles solves with REGION.md routing — worth comparing the trade-offs. The **16 orchestrators** are also worth mining for multi-agent workflow templates that go beyond agentfiles' current single-dispatch pattern.
