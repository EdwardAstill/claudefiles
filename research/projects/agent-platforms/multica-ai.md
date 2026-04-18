# multica-ai/multica

**URL:** https://github.com/multica-ai/multica
**Type:** Managed Agents Platform

## What It Is

An open-source "managed agents platform" that treats AI agents as human-like teammates. It provides a dashboard and daemon to assign tasks, track progress across multiple agents (Claude Code, Codex, etc.), and manage their lifecycle.

---

## What It Does Well

- **Fleet Orchestration** — Provides the infrastructure to manage multiple agents as a cohesive team.
- **Cross-Agent Visibility** — A unified dashboard to see what every agent is working on, their logs, and their progress.
- **Lifecycle Management** — Handles the "daemonization" of agents, allowing them to run long-running tasks in the background.
- **Teammate Abstraction** — Shifts the mental model from "running a script" to "assigning a task to a teammate."

---

## Weaknesses

- **Infrastructure Overhead** — Requires running a dashboard and daemon, which is more complex than a standalone CLI tool.
- **Dependency on Centralized Platform** — Even though it's open source, the "platform" model is less portable than a simple dotfiles/skills repository.
- **Abstraction Gap** — Can sometimes hide the low-level CLI errors that are critical for debugging.

---

## What agentfiles Could Learn

| Idea | How to Apply |
|------|-------------|
| **Background Agents** | Add support to `af worktree` or the `manager` to spawn "background" subagents that report back via notifications or a status file. |
| **Progress Tracking** | Formalize how the `manager` tracks sub-task progress in `.agentfiles/`, making it visible to the user without reading verbose logs. |
| **Teammate Personas** | Add "persona" metadata to skills (e.g., "The Security Auditor," "The Rust Specialist") to make multi-agent coordination feel more like a team effort. |
