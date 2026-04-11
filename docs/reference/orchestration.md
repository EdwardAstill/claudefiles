# Orchestration Reference

How claudefiles routes work, why each design choice was made, and where the system
has known gaps.

---

## The Flow

```
Session start
    └─ using-claudefiles (establishes skill-checking discipline)

Every new task
    └─ executor
           1. Orient    — cf context + cf status (MANDATORY)
           2. Assess    — parallel agents needed? (almost never)
           3. Plan      — 2–4 lines for non-trivial tasks
           4. Execute   — load specialists inline as needed
           5. Verify    — MANDATORY: run tests, check output, report evidence
           6. Escalate  — if needed: HANDOFF CONTEXT block → manager

           ┊  escalate only when genuinely parallel work is needed
           ▼

manager
    Phase 1 — Plan
        Read HANDOFF CONTEXT from executor (cf context, cf status, work done so far)
        Read relevant REGION.md files
        Three questions (load advisors inline if non-obvious):
            design-advisor       → brainstorming or spec first?
            git-advisor          → worktrees, branches, PRs?
            coordination-advisor → parallel vs sequential? dependencies?
        Confirm plan with user.

    Phase 2 — Execute
        Parallel work    → Agent tool (multiple calls in one message)
        Sequential+gates → subagent-driven-development
        Single domain    → individual specialist subagent

    Phase 3 — Review + Replan
        Check for conflicts between agent outputs
        Run full test suite
        Adaptive replan if agents fail or discover unexpected info
```

---

## Layer by Layer

### using-claudefiles — session-start enforcement

**What it does:** Fires at session start. Establishes executor as the default entry
point and documents how skills are invoked.

**Why it exists:** Without it, the skill system is opt-in and the most powerful skills
(systematic-debugging, tdd, brainstorming) are the ones most likely skipped under pressure.

**Limitation:** Depends on Claude Code loading the skill at session start. If compressed
or missing, enforcement fails silently.

---

### executor — single-agent default

**What it does:** Entry point for every new task. Orients, assesses, plans briefly,
executes with full tool access, and verifies before reporting.

**Why single-agent is default:** A single agent with full context outperforms a
coordinated team for the vast majority of tasks. Parallelism has real overhead: each
agent starts from scratch, outputs must be synthesized, and conflicts resolved. Most
work that feels "complex" is just deep — handled better by one agent with full context.

**Why specialists load inline:** Subagents lose session state. Inline `Skill()` loading
brings specialist knowledge into the existing conversation where executor already knows
the task, constraints, and history. Context is irreplaceable.

**Why verification is mandatory:** Without explicit enforcement, "the code is clearly
correct" skips verification and bugs ship. Step 4 requires evidence: command output,
test results, or observable behavior. Phrases like "should work" are not evidence.

**Why HANDOFF CONTEXT on escalation:** Context loss is the #1 failure mode in
multi-agent systems. When executor escalates, it passes a structured block containing
cf context output, cf status output, work completed, and why escalation is needed.
This prevents manager from starting blind.

**Specialist skills available (load inline):**

| Category | Skills |
|----------|--------|
| Languages | `python-expert`, `typescript-expert`, `rust-expert`, `typst-expert` |
| Quality | `tdd`, `systematic-debugging`, `verification-before-completion`, `code-review`, `simplify`, `security-review`, `performance-profiling`, `refactoring-patterns`, `dependency-management`, `observability`, `accessibility` |
| Data | `database-expert` |
| Infrastructure | `infrastructure-expert` |
| Version control | `git-expert`, `github-expert`, `github-actions-expert` |
| API | `api-architect` |
| Research | `docs-agent`, `research-agent`, `codebase-explainer` |

**Limitation:** One context window has limits. Very large tasks (20+ independent
subtasks across genuinely unrelated domains) will see context degradation — this is
when manager is appropriate, but it is a high bar.

---

### manager — multi-agent coordinator

**What it does:** Reads handoff context, runs a planning phase, confirms with the user,
dispatches agents, then reviews results with adaptive replanning.

**Why planning comes first:** Agent dispatch is expensive to undo. Structural problems
compound once execution starts. Planning upfront with user confirmation catches them.

**Why the high escalation bar:** Coordination overhead is real. Each agent must be
briefed from scratch, outputs synthesized, conflicts resolved. Multi-agent systems
consume ~15x more tokens than single-agent for the same task. For work that can be
done sequentially, manager adds cost without benefit.

**Phase 3: Review + Replan (new):** After agents complete, manager checks for conflicts,
runs the full test suite, and evaluates results. If an agent failed or discovered
something that invalidates the plan, manager replans rather than forcing the original
plan. Plans are hypotheses; execution is the experiment.

| Situation | Replan action |
|-----------|---------------|
| Agent failed on a task | Analyze why, re-dispatch with better context |
| Agent discovered design flaw | Pause remaining agents, re-evaluate plan |
| Agent outputs conflict | Make conflicting tasks sequential, re-dispatch |
| 3+ agents failed on related tasks | Stop — structural problem, re-run planning |

---

### The Three Advisors

| Advisor | Single mandate |
|---------|---------------|
| `design-advisor` | Does this need brainstorming or a spec before implementation? |
| `git-advisor` | What git strategy: worktrees, branches, PRs, commit structure? |
| `coordination-advisor` | Parallel vs sequential? Dependencies? Team composition? |

**Why three narrow advisors:** Role-priming research shows agents given a single mandate
produce deeper analysis than generalists covering multiple domains. Each advisor also has
a narrower failure mode — a gap in one area doesn't contaminate the whole plan.

**Why inline, not subagents:** Planning requires the full task context. Subagent dispatch
loses it.

**Why optional:** Not every question is non-obvious. Loading git-advisor when the answer
is clearly "commit to main" adds tokens without insight.

---

## What the System Doesn't Do

**No automated agent output merging.** Parallel agents return independently. Synthesis
is manual: read summaries, check conflicts, run tests, resolve divergence.

**No automatic mid-task re-routing.** If executor discovers manager would be better,
it escalates with HANDOFF CONTEXT. The handoff requires a deliberate step, not automatic
transfer.

**No skill quality testing.** `cf check` verifies REGION.md entries exist. It cannot
verify that a skill's content is accurate or well-calibrated. Skills can drift silently.

**No context pressure monitoring.** Loading multiple specialists in a long session fills
context gradually. The system doesn't track this or warn when context is tight.

**Passive enforcement.** `using-claudefiles` establishes rules at session start but
doesn't actively block non-compliant behavior — it depends on the rules being read and
followed.
