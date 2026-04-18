# coleam00/Archon

**URL:** https://github.com/coleam00/Archon
**Type:** Workflow engine / coding agent platform

## What it is

A workflow engine that makes AI coding deterministic. Defines agent execution as a directed acyclic graph (DAG) of nodes — plan, implement, validate, review, loop, pause — forcing the agent through proven phases rather than relying on the model's "mood." Ships as a full platform you can run, and can also be installed as a skill into Claude Code, Gemini CLI, and other runtimes.

## How it works (2026-04-18 snapshot)

- **DAG workflows, not sequential phases.** Nodes declare `depends_on`, so workflows can fan out, join, and branch. Much more flexible than the "Plan → Implement → Validate → Review" framing the previous write-up described.
- **Loop nodes with fresh context per iteration.** A node can loop `until: ALL_TASKS_COMPLETE` and reset context between iterations — an explicit hallucination-prevention pattern where each loop body sees only what it needs.
- **Interactive human gates.** Pause nodes halt the workflow until an explicit human approval. Not optional polish; treated as a first-class workflow primitive.
- **17 bundled workflows.** `archon-fix-github-issue`, `archon-idea-to-pr`, and others ship preconfigured. Workflow definition is not purely a user responsibility.
- **Unified message bus + event log.** Work routes through Web UI, CLI, Telegram, Slack, Discord, and GitHub simultaneously. Same workflow can be driven from any surface.
- **Database persistence.** SQLite / PostgreSQL state across 7 tables. Workflows can be long-lived and async; state survives restarts.
- **Context isolation via git worktrees.** Each workflow task gets its own worktree so branches don't contaminate each other.

## Notable patterns

- **DAG with explicit `depends_on`.** Workflow shape is first-class data, not procedural code. Enables dry-run visualisation and partial replay.
- **Fresh context per loop iteration.** The most valuable pattern here for agent reliability — "run N times with different inputs, each run sees a clean slate" is rare outside Archon.
- **Bundled workflows are part of the product.** Lowers the config burden users historically paid.
- **Single event bus across six interfaces.** Work can start in Telegram, resume in Web UI, finish in GitHub.
- **Pause-nodes as primitives.** Treats "ask the human" as a state, not a tool call.

## Weaknesses

- **Configuration heavy.** YAML workflows are more up-front effort than a quick prompt.
- **Overhead for small tasks.** Phase enforcement feels slow for expert users who could skip steps.
- **Platform ambition.** Running the full Archon server (with DB, bus, web UI) is a commitment — adopting just the YAML/DAG idea is lighter.

## Take-aways for agentfiles

Archon's patterns align strongly with our executor/manager orchestration. Adopt ideas, not the platform:

1. **Loop nodes with fresh context** — the highest-leverage steal. Our `subagent-driven-development` skill could formalise "loop this task N times on N inputs, fresh subagent each iteration" as an explicit mode. Prevents drift on batch operations like migrations or per-file edits.
2. **Machine-readable plan output.** `writing-plans` currently produces human markdown. Add a companion YAML/JSON block (schema: ordered nodes with `depends_on`, gates, completion criteria) that `subagent-driven-development` can execute without re-parsing prose. Cheap and aligns with our existing plan format.
3. **Pause nodes as a first-class step type.** Plans today list steps; none of them say "stop and ask the user." Make that explicit — `{type: pause, prompt: "..."}` — so plans can encode their own human-checkpoints.
4. **Bundled workflows.** `task-archetypes.md` already lists 15 patterns. Promote the top 3–5 to actual runnable plans stored at `docs/plans/archetype-<name>.yaml`, invocable via `af archetype run <name>`.

Skip: the full platform, the web UI, the multi-channel bus, the Postgres/SQLite persistence. Our "plans live as markdown in the repo" philosophy is lighter and works for our scale.

**Last checked:** 2026-04-18
