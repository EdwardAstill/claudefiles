# wshobson/agents

**URL:** https://github.com/wshobson/agents
**Type:** Agent Library & Orchestrator

## What It Is

A massive repository featuring 182 specialized agents and 16 multi-agent workflow orchestrators. It uses a custom plugin system (`/plugin marketplace add wshobson/agents`) to allow users to load only the specific agents or tools they need for a given task.

---

## What It Does Well

- **Sheer Volume** — One of the largest collections of specialized agent prompts (182+) covering almost every imaginable niche (e.g., "Postgres Optimizer," "React Native Expert").
- **Plugin Architecture** — The "marketplace" concept is a very sophisticated way to manage a large skill/agent suite without bloating the context window.
- **Multi-Agent Workflows** — Includes 16 pre-defined orchestrators that know how to chain specific agents together for complex sprints.
- **Active Community** — High frequency of updates and a strong contributor base.

---

## Weaknesses

- **Quality Variance** — With 180+ agents, the quality and "vibe" of the prompts can vary significantly.
- **Complexity** — The custom plugin system adds a layer of abstraction that requires learning its specific syntax and commands.
- **Context Management** — While the plugin system helps, running multiple specialized agents still risks context fragmentation if not managed carefully.

---

## What agentfiles Could Learn

| Idea | How to Apply |
|------|-------------|
| **Plugin Marketplace** | Implement a command (e.g., `af add <skill-name>`) that pulls individual skills from a central repository into the local `.claude/skills/` folder. |
| **Agent Chaining** | Add "recipe" files to the `manager` that define specific sequences of agents (e.g., "New Feature" = Brainstorming -> Spec-Kit -> Rust-Expert -> PR-Reviewer). |
| **Narrow Specialization** | Decompose broad skills (like `python-expert`) into narrower ones (e.g., `fastapi-expert`, `pandas-expert`) for even higher precision. |
