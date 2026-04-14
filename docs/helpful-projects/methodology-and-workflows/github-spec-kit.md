# Spec Kit (GitHub)

**URL:** https://github.com/github/spec-kit
**Type:** Spec-Driven Development Toolkit

## What It Is

An open-source toolkit for "Spec-Driven Development." It provides a structured workflow for agents using `/specify`, `/plan`, and `/tasks` commands to steer them through a rigorous implementation process. It focuses on turning high-level goals into concrete, verifiable implementation steps.

---

## What It Does Well

- **Process Rigor** — Forces a strict separation between "What" (Specify), "How" (Plan), and "Action" (Execute).
- **Verifiable Tasks** — Encourages the creation of small, atomic tasks that each have a clear "Definition of Done."
- **Standardized Commands** — Uses a clean, slash-command based interface that is very intuitive for users coming from Cursor or Copilot.
- **High Success Rate** — By forcing the "Plan" phase, it significantly reduces the rate of agents wandering off-track or hallucinating.

---

## Weaknesses

- **Manual Effort** — Requires the user to participate heavily in the "Specify" and "Plan" phases, making it less "hands-off."
- **Verbosity** — The structured approach can generate a lot of documentation (Specs, Plans) which might be overkill for small features.
- **Tooling Lock-in** — The workflow is optimized for the GitHub ecosystem and specific "Spec Kit" commands.

---

## What agentfiles Could Learn

| Idea | How to Apply |
|------|-------------|
| **Formal `/specify` Phase** | Enhance the `brainstorming` skill to produce a formal "Spec Document" that is explicitly referenced by all subsequent skills. |
| **Atomic Task Tracking** | Add a `task.json` to `.agentfiles/` that tracks the status (Todo/Doing/Done) of every sub-task in a plan. |
| **Definition of Done** | Require every task in a `writing-plans` output to include a "Verification Script" or command. |
