---
name: manager
description: >
  Use only when work genuinely needs parallel multi-domain agents. Trigger
  phrases: "coordinate multiple agents on this", "run frontend and backend in
  parallel", "dispatch agents across repos X and Y at the same time", "this is
  too big for one context", "20+ independent subtasks across unrelated areas",
  "executor escalated to manager", "orchestrate a multi-agent build". Runs one
  planning review pass (design, git strategy, coordination — pulling advisors
  inline only for non-obvious calls), confirms plan with user, then dispatches.
  Do NOT use for complex-but-sequential work in one domain (use executor) or
  for executing an already-written plan in the current session (use
  subagent-driven-development).
---

# Manager

Coordinator for work that genuinely requires multiple agents. Two phases: plan, then
dispatch.

**Model:** Use the most capable available model (Opus or equivalent).

## Phase 1: Plan

### Read handoff context

If executor escalated here, look for the **HANDOFF CONTEXT** block. It contains:
- The original user request
- af context and af status output (so you don't re-run them)
- Work completed before escalation
- Why parallelism is needed

If no handoff block exists (direct invocation), run af context and af status yourself.

### Read relevant regions

Identify which categories are involved and read their REGION.md files:

```bash
cat agentfiles/coding/REGION.md      # if implementation work involved
cat agentfiles/planning/REGION.md    # if design/spec work involved
cat agentfiles/research/REGION.md    # if research involved
```

### Check the task-archetypes registry

Before planning from scratch, match the user's intent against the registry:

```bash
af archetype match "<quoted user intent>"   # ranked candidates + phase layout
af archetype show <id>                      # full layout for one archetype
```

The registry lives at `docs/reference/task-archetypes.json` (human-readable
companion at `docs/reference/task-archetypes.md`). It maps common big-task shapes to
agent group compositions — phases, which agents run per phase, parallel vs sequential,
risks.

- If a candidate scores well, start from that archetype's phase layout rather than
  designing one from scratch. Adapt; don't copy blindly.
- If no archetype fits, proceed to the planning pass below. If the task looks like a
  recurring shape that isn't in the registry yet, add it after the work is done.

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

## Phase 3: Review and Replan

After agents complete, review results before reporting success:

1. **Check for conflicts** — did any agents touch the same files? Resolve before continuing.
2. **Run full test suite** — verify the combined output works together.
3. **Check for discoveries** — did any agent report unexpected findings that invalidate
   the plan?

### Adaptive replanning

If an agent fails or discovers something that changes the plan:

| Situation | Action |
|-----------|--------|
| Agent failed on a task | Analyze why. Re-dispatch with better context, or reassign to a different skill. |
| Agent discovered a design flaw | Pause remaining agents. Re-evaluate the plan. Update and re-dispatch if needed. |
| Agent's output conflicts with another's | Make conflicting tasks sequential instead of parallel. Re-dispatch the later one with the earlier one's output as context. |
| 3+ agents failed on related tasks | Stop. The plan has a structural problem. Re-run the planning phase with what you've learned. |

**Do not force the original plan when reality contradicts it.** Plans are hypotheses.
Execution is the experiment. Update the plan when the experiment reveals new information.

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
