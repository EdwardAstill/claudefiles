# SuperClaude-Org/SuperClaude_Framework

**URL:** https://github.com/SuperClaude-Org/SuperClaude_Framework
**Stars:** ~20,000 | **Type:** Meta-programming configuration framework

## What It Is

The most architecturally ambitious comparable project. A full "meta-programming configuration framework" built from `.md` instruction files:
- 30 slash commands (`/sc:research`, `/sc:implement`, `/sc:test`)
- 20 specialized agent **personas** (PM, Security Engineer, Frontend Architect) — not just prompts; each has defined tools, context, and model preferences
- 7 **adaptive behavioral modes** (brainstorming, deep-research, token-efficiency, orchestration, etc.)
- Optional MCP server integration that claims 2-3x performance improvement
- Distributed as a PyPI package: `pip install superclaude && superclaude install`

---

## What It Does Well

- **Behavioral modes** — switching the AI's entire operating *posture* (not just routing to a skill) is a qualitatively different idea. Token-efficiency mode changes how terse Claude is. Deep-research mode changes how many sources it consults. This is orthogonal to skill routing.
- **Agent personas with model preferences** — 20 named specializations where each persona declares which Claude model it prefers (Opus for architecture review, Sonnet for coding). The skill + model pairing is explicit.
- **Documentation-driven project state** — systematic use of `PLANNING.md`, `TASK.md`, `KNOWLEDGE.md` as live shared context files between agents.
- **PyPI distribution** — zero-friction install makes adoption very low-cost.

---

## Weaknesses

- Performance is MCP-dependent — "standard performance" without MCPs, claims "2-3x improvement" with them. Fragile if MCPs are unavailable.
- No executor/routing concept — user must manually choose the right `/sc:` command from 30 options
- Commands don't chain or escalate — limited composability
- TypeScript plugin system for improved distribution has no ETA (stuck at v4 planning)

---

## What agentfiles Could Learn

| Idea | How to Apply |
|------|-------------|
| **Behavioral modes** | A `mode: token-efficient` or `mode: deep-research` concept in agentfiles that changes executor's verbosity, source depth, and verification thoroughness — separate from skill routing |
| **Documentation-driven project state** | `af init` already seeds `.agentfiles/`. Could add a `PLANNING.md` convention for executor to read/write during multi-step tasks |
| **Agent model preferences in manifest** | `manifest.toml` could include `model = "opus"` per skill, and `af setup` could warn if the current session model doesn't match heavy-weight skills |
| **PyPI-style distribution** | `af install` already delegates to `install.sh`. A `pip install agentfiles` or `brew install agentfiles` shim would reduce the bootstrap friction further |
