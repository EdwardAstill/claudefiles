# GitHub Next: Agentic Workflows

**URL:** https://github.com/github/agentic-workflows
**Type:** CI/CD Automation Framework

## What It Is

A technical preview from GitHub Next that allows developers to write repository automation in Markdown instead of YAML. Agents run in sandboxed GitHub Actions to handle tasks like issue triaging, PR reviews, and automated maintenance.

---

## What It Does Well

- **Markdown-Based Logic** — Allows non-engineers (or engineers who hate YAML) to write automation in a readable, natural-language format.
- **Native GitHub Integration** — Deeply integrated into the GitHub ecosystem, leveraging Actions, Issues, and PRs natively.
- **Sandboxed Execution** — Runs in isolated environments with specific permissions, ensuring safety for autonomous tasks.
- **Readable Execution Logs** — Because the "code" is Markdown, the execution traces are much easier for humans to follow and audit.

---

## Weaknesses

- **Early Access** — Currently in technical preview, which means APIs and features are subject to significant change.
- **GitHub Dependency** — Strictly limited to the GitHub platform; cannot be easily run locally or on GitLab/Bitbucket.
- **Latency** — Running agents as GitHub Actions adds significant overhead and latency compared to local CLI execution.

---

## What agentfiles Could Learn

| Idea | How to Apply |
|------|-------------|
| **Markdown Actions** | Allow `agentfiles` to "execute" a Markdown file as a series of steps (similar to how it already reads `SKILL.md`). |
| **Permission-Scoped Agents** | Add metadata to skills that defines which shell commands or directories they are allowed to access (a "Sandbox Lite"). |
| **Issue-to-Task Conversion** | Create a skill that can read a GitHub issue and automatically generate an `af worktree` and an implementation plan. |
