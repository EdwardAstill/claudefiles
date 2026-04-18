# NousResearch/hermes-agent

**URL:** https://github.com/NousResearch/hermes-agent
**Type:** Autonomous Agent & Skill Suite

## What It Is

A self-improving AI agent designed for long-term autonomy. It features a "learning loop" where it creates and refines skills based on experience, builds a persistent model of the user, and supports multiple interfaces (TUI, Telegram, Discord). It follows the `agentskills.io` standard for skill organization.

---

## What It Does Well

- **Procedural Memory / Learning Loop** — The agent can "learn" new CLI commands and workflows autonomously, recording successful patterns into its skill library.
- **Skill Portability** — Uses the `agentskills.io` standard, making skills easier to share across different agent runtimes.
- **Multi-Interface Support** — Not limited to a CLI; can be interacted with via TUI, Telegram, or Discord.
- **Persistent User Modeling** — Builds a long-term understanding of the user's preferences and environment.

---

## Weaknesses

- **Complexity** — The "learning loop" adds significant overhead and requires more careful monitoring than static skill suites.
- **Resource Intensive** — Long-term memory and constant skill refinement can lead to high token usage and context management challenges.
- **Experimental** — Many of the "self-improvement" features are still in early stages and can produce hallucinated or low-quality skills.

---

## What agentfiles Could Learn

| Idea | How to Apply |
|------|-------------|
| **Skill Learning Loop** | Implement a command (e.g., `af learn`) that analyzes a successful multi-turn session and generates a draft `SKILL.md` for that workflow. |
| **agentskills.io Compatibility** | Align `manifest.toml` and `SKILL.md` formats with emerging standards to allow importing/exporting skills from other ecosystems. |
| **Persistent Context** | Use the `.agentfiles/notes.md` or a dedicated user profile file to track non-project-specific user preferences (e.g., "always use standard library over external dependencies"). |
