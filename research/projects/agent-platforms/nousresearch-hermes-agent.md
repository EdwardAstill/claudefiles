# NousResearch/hermes-agent

**URL:** https://github.com/NousResearch/hermes-agent
**Type:** Autonomous agent platform + skill suite

## What it is

A self-improving AI agent built for long-term autonomy. Core loop: it creates and refines skills from experience, builds a persistent model of the user, and exposes itself across many surfaces simultaneously. Originally positioned as local-first; current state is deployment-agnostic.

## How it works (2026-04-18 snapshot)

- **Model flexibility.** 200+ models via OpenRouter, NVIDIA NIM, Xiaomi MiMo, plus direct provider APIs. Not tied to one vendor.
- **Execution surface.** Runs in-process, in Docker, via SSH, or serverlessly on Daytona, Singularity, or Modal — with hibernation so long-lived agents sleep between events.
- **Interface sprawl.** A unified gateway process fans out over Telegram, Discord, Slack, WhatsApp, Signal, CLI, and a TUI — so the same agent identity is reachable from seven channels at once. Voice memos are transcribed; conversations persist across channels.
- **Orchestration.** Parallel subagent spawning for isolated workstreams, a built-in cron scheduler for time-triggered runs, and research-ready batch trajectory generation + RL environments for training/eval.
- **Memory architecture.** SQLite FTS5 session search with LLM summarisation for cross-session recall, plus Honcho dialectic user modelling — a named framework rather than ad-hoc "persistent preferences."
- **Skill system.** Follows the `agentskills.io` standard for portability; "learning loop" observes successful multi-turn interactions and drafts new skills from them.

## Notable patterns

- **Gateway-per-identity.** One process multiplexes channels, so routing/policy lives in one place instead of each adapter reimplementing it.
- **Hibernatable agents.** Explicit serverless+hibernation pattern — the agent isn't "up" so much as "resumable."
- **Dialectic user model.** Honcho-style continuous refinement beats a static preferences file.
- **Trajectory + RL hooks at the same level as memory.** Treats the session log as training data, not just a retrieval corpus.

## Weaknesses

- **Complexity.** Many moving parts (gateway, scheduler, hibernation, Honcho, trajectory pipeline) mean significant monitoring surface.
- **Resource intensive.** Persistent memory + constant skill refinement + multi-channel presence push token usage and context-management difficulty.
- **Experimental self-improvement.** Skill-creation loop still produces low-quality / hallucinated skills often enough that human review is mandatory before promotion.

## Take-aways for agentfiles

Agentfiles doesn't need a gateway, multi-channel presence, or serverless hibernation — those solve deployment problems we don't have. What's worth lifting:

1. **Named skill-learning loop.** `af learn` could read `af log review` output for successful multi-turn patterns and draft a candidate `SKILL.md`, saved to `docs/skills-drafts/`. Aligns with hermes's "observe successful interactions → draft skill" and explicitly gated on human promotion.
2. **Dialectic user model as a discipline, not a framework.** We already have `.agentfiles/notes.md` and `CLAUDE.md`. The lesson is to treat user-preference capture as *continuous refinement* rather than append-only. A retrospective-skill output that proposes edits to existing preferences beats appending another one.
3. **Parallel-subagent-for-isolated-workstreams** is already our manager pattern — confirmed relevant, no action needed.
4. **Align `manifest.toml` + `SKILL.md` with `agentskills.io` when the standard stabilises.** Current fork points are minor; revisit when the spec is versioned.

Skip: the gateway, voice transcription, cron, hibernation, RL trajectory pipeline. They solve problems downstream of where agentfiles sits.

**Last checked:** 2026-04-18
