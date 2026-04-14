# coleam00/Archon

**URL:** https://github.com/coleam00/Archon
**Type:** Workflow Engine / Coding Agent

## What It Is

A workflow engine that makes AI coding deterministic. It uses YAML-defined workflows to force agents through specific phases (Plan → Implement → Validate → Review) rather than relying on the model's "mood." It can be installed as a skill into existing agents.

---

## What It Does Well

- **Deterministic Workflows** — Uses rigid YAML definitions to ensure the agent follows a proven engineering process every time.
- **Phase-Based Execution** — Explicitly separates planning, implementation, and verification, preventing the agent from "rushing" to code.
- **Context Isolation** — Uses git worktrees and isolated environments to prevent "context contamination" between tasks.
- **Extensible as a Skill** — Can be integrated into other agent runtimes like Claude Code or Gemini CLI.

---

## Weaknesses

- **Rigidity** — The YAML-based approach can be too restrictive for simple tasks or creative problem-solving.
- **Configuration Heavy** — Setting up complex workflows in YAML can be more time-consuming than just describing the task.
- **Overhead** — The strict enforcement of phases can feel "slow" for expert users who want to skip certain steps.

---

## What agentfiles Could Learn

| Idea | How to Apply |
|------|-------------|
| **YAML-Defined Plans** | Allow `writing-plans` to output a machine-readable plan (YAML/JSON) that the `manager` or `subagent-driven-development` can use to enforce step-by-step execution. |
| **Hard Verification Gates** | Implement mandatory check-scripts defined in a plan that must pass before the `executor` can proceed to the next phase. |
| **Isolated Execution** | Standardize the use of git worktrees for *all* subagent tasks to ensure a clean state and easy rollbacks. |
