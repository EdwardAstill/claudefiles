---
name: complex-orchestrator
description: >
  Full planning and coordination layer. Invoked by simple-orchestrator when a task scores
  HIGH on scope, research/context, or agent coordination. Reads dev-suite/registry.md for
  complete skill input/output contracts, then plans and executes multi-skill workflows
  including worktree setup and parallel agent dispatch.
---

# Complex Orchestrator

The planning brain for high-complexity tasks. Called by simple-orchestrator; never invoked
directly by the user. Reads the full registry to understand skill contracts, then produces
and executes a coordinated plan.

## On Invocation

Before planning, read the agent bus if it exists:

```bash
cf-context --write   # project fingerprint
cf-status --write    # git topology
cf-note --read       # any findings from prior agents this session
```

This gives full situational awareness before touching anything.

## Inputs (from simple-orchestrator)

- User's goal (verbatim or summary)
- Which complexity axes scored HIGH
- Any known context (current branch, active worktrees, recent work)

## Process

```dot
digraph complex_orchestrator {
    "Receive escalation" [shape=doublecircle];
    "Read registry.md" [shape=box];
    "Clarify goal if ambiguous" [shape=box];
    "Goal clear?" [shape=diamond];
    "Plan execution" [shape=box];
    "Present plan to user" [shape=box];
    "User approves?" [shape=diamond];
    "Revise plan" [shape=box];
    "Execute: dispatch skills/agents" [shape=box];
    "Collect outputs, hand off results" [shape=box];
    "Done" [shape=doublecircle];

    "Receive escalation" -> "Read registry.md";
    "Read registry.md" -> "Clarify goal if ambiguous";
    "Clarify goal if ambiguous" -> "Goal clear?";
    "Goal clear?" -> "Plan execution" [label="yes"];
    "Goal clear?" -> "Clarify goal if ambiguous" [label="no, ask user"];
    "Plan execution" -> "Present plan to user";
    "Present plan to user" -> "User approves?";
    "User approves?" -> "Execute: dispatch skills/agents" [label="yes"];
    "User approves?" -> "Revise plan" [label="no"];
    "Revise plan" -> "Present plan to user";
    "Execute: dispatch skills/agents" -> "Collect outputs, hand off results";
    "Collect outputs, hand off results" -> "Done";
}
```

## Reading the Registry

The registry is at `dev-suite/registry.md` relative to the claudefiles repo root.
Read it to understand:
- What each skill expects as **inputs**
- What each skill produces as **outputs**
- How skills **chain** (which skill's output feeds the next skill's input)
- What **tools** each skill requires

## Planning Rules

1. **Prefer sequential over parallel** when skills share state (e.g., git-expert must run before other skills that need a worktree path)
2. **Prefer parallel** when skills are independent (e.g., docs-agent + research-agent can run simultaneously)
3. **Set up git context first** — if any skill needs a worktree, invoke git-expert first and capture its output before proceeding
4. **Always present the plan** before executing. Include: which skills, in what order, why.
5. **Checkpoint after each skill** — verify output matches expected before feeding to the next skill

## Execution

- Use the `dispatching-parallel-agents` skill when launching multiple independent agents
- Use the `subagent-driven-development` skill when executing a sequential plan in the current session
- Capture outputs explicitly and pass them as inputs to downstream skills

## Output

At completion, summarise:
- What was done
- What each skill produced
- Any worktrees created (paths + branches)
- Any follow-up actions the user should take

## Anti-patterns

| Thought | Reality |
|---------|---------|
| "I'll figure out the plan as I go" | Read the registry first. Plan before acting. |
| "These skills can probably run in parallel" | Check for shared state. Parallel only when truly independent. |
| "The user's goal is clear enough" | If any ambiguity could cause rework, ask before executing. |
| "I'll skip the plan presentation to save time" | Never. User must approve before execution. |
