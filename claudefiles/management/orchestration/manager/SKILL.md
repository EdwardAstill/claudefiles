---
name: manager
description: >
  Use when executor escalates here — genuinely multi-agent work: parallel domains,
  or scale so large a single context degrades. Runs a single planning review pass,
  then dispatches agents. Not for complex-but-sequential work (that's executor).
---

# Manager

Coordinator for work that genuinely requires multiple agents. Two phases: plan, then
dispatch.

**Model:** Use the most capable available model (Opus or equivalent).

## Phase 1: Plan

### Read relevant regions

Identify which categories are involved and read their REGION.md files:

```bash
cat claudefiles/coding/REGION.md      # if implementation work involved
cat claudefiles/planning/REGION.md    # if design/spec work involved
cat claudefiles/research/REGION.md    # if research involved
```

### Single planning review pass

Do one pass covering all three questions — don't split into sequential consultants:

1. **Design/spec?** Does this need brainstorming or a written spec before implementation?
   If yes, brainstorming runs first and produces a spec before any agents start coding.

2. **Git strategy?** Isolated worktrees per agent? One shared branch? PR at end?
   What commit structure makes sense?

3. **Coordination?** Which agents run in parallel vs sequentially? What does each
   agent produce, and does any agent depend on another's output?

If any question needs deeper analysis, load the relevant advisor inline — each has a
single focused mandate:
- `design-advisor` — does this need brainstorming or a written spec first?
- `git-advisor` — what git strategy fits: worktrees, branches, PRs, commit structure?
- `coordination-advisor` — which agents run in parallel vs sequentially?

Load only the advisors relevant to non-obvious decisions. Answer obvious ones inline.

### Confirm with the user

Present the plan before executing:
- Which agents run, in what order (or in parallel)
- What each produces
- How outputs feed into the next step

Wait for confirmation.

## Phase 2: Execute

**Parallel agents** — use the Agent tool, multiple calls in one message:
- One agent per independent problem domain
- Each gets focused context: specific scope, clear goal, expected output format
- No shared state between agents — if agents would edit the same files, make them sequential
- After all return: review summaries, check for conflicts, run full test suite

**Sequential with review gates** — use `subagent-driven-development`:
- Each task gets a fresh subagent + two-stage review before proceeding
- Use when tasks depend on each other's output or share state

**Individual specialist** — dispatch as a single subagent for focused domain work.

## Advisors vs Specialists

| | Advisors (`design-advisor`, `git-advisor`, `coordination-advisor`) | Specialists |
|---|---|---|
| **When** | Planning phase only, if needed | Execution phase |
| **How** | Loaded inline | Dispatched as subagents |
| **Purpose** | Advise on plan structure | Do the work |

Never dispatch advisors as subagents. Never load a specialist for planning.

## What belongs here vs executor

**Manager:** brainstorming + api design + Rust implementation + deployment config,
all in parallel, outputs feeding each other.

**Executor:** complex Rust implementation with database work and tests — deep, but
one agent can hold it in context and work through it sequentially.

When in doubt, start with executor. Escalate to manager only if the agent gets
overwhelmed or parallelism becomes the bottleneck.
