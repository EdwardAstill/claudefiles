# gsd-build/get-shit-done

**URL:** https://github.com/gsd-build/get-shit-done
**Type:** Context Engineering / Skill Suite

## What It Is

A "context engineering" and meta-prompting system designed to solve "context rot." It breaks large projects into atomic phases and plans, ensuring the agent always operates within a fresh, relevant context window. It installs as a suite of skills.

---

## What It Does Well

- **Context Management** — Excellent at preventing the "long-session slowdown" by aggressively rotating context and focusing on atomic sub-tasks.
- **Phase-Based Planning** — Uses specialized commands like `/gsd-plan-phase` to maintain a high-level project map while working on low-level details.
- **Recursive Task Breakdown** — Very strong at decomposing complex requests into manageable pieces that don't exceed the model's reliable attention span.
- **Built for Scale** — Explicitly designed for large-scale migrations or feature builds that span many files and many hours.

---

## Weaknesses

- **Verbose Prompting** — The meta-prompts and phase-management can consume a lot of tokens if not managed carefully.
- **Proprietary/Opinionated Logic** — The "GSD way" of working is very specific and might conflict with a user's existing habits.
- **Manual Overhead** — Requires the user to be active in "advancing" the phases, which can feel less "autonomous."

---

## What agentfiles Could Learn

| Idea | How to Apply |
|------|-------------|
| **Phase Rotation** | Implement a "Context Reset" mechanism in the `manager` that clears unnecessary historical context between major project phases. |
| **Atomic Planning** | Have `writing-plans` generate "atomic task blocks" that include their own localized context requirements (which files to read, which docs to check). |
| **Project Map** | Maintain a `plan.md` in `.agentfiles/` that acts as the "Source of Truth" for the current phase, which every skill reads to stay oriented. |
