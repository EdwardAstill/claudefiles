# Melty Labs: Conductor

**URL:** https://github.com/meltylabs/conductor
**Type:** Desktop Orchestrator (macOS)

## What It Is

A macOS-native orchestrator that provides a visual dashboard for running multiple Claude Code agents in parallel. Each agent runs in its own isolated git worktree, and the "Conductor" provides a unified UI for reviewing diffs, running tests, and managing the fleet.

---

## What It Does Well

- **Visual Dashboard** — Provides a clear, real-time view of what every agent is doing, which is much more intuitive than tailing multiple terminal logs.
- **Isolated Execution** — Strictly enforces one agent per worktree, which is the "gold standard" for preventing context contamination.
- **Diff Management** — Includes a sophisticated UI for reviewing and merging changes from multiple agents simultaneously.
- **Native Experience** — Leverages macOS features for notifications and system integration, making the agent feel like part of the OS.

---

## Weaknesses

- **Platform Locked** — Being a native macOS app, it is not available for Linux or Windows users.
- **Closed Source (Core)** — While the repo contains extensions, the core orchestrator is not as "hackable" as a pure CLI tool like `agentfiles`.
- **UI Dependency** — Less suitable for remote/SSH development where a GUI isn't available.

---

## What agentfiles Could Learn

| Idea | How to Apply |
|------|-------------|
| **Visual TUI** | Add a "Dashboard" command to the `af` CLI (using a library like `Textual`) that shows a live view of all active worktrees and agent statuses. |
| **Unified Diff Review** | Create a skill that gathers all changes from parallel worktrees and presents them as a single, categorized diff for the user. |
| **Notification Support** | Add system notifications (via `notify-send` or similar) when an agent completes a task or hits an error. |
