# Orchestration Reference

How claudefiles routes work, why each design choice was made, and where the system
has known gaps.

---

## The flow

```
Session start
    └─ using-claudefiles (system-reminder enforcement)
           Establishes: check for applicable skills before any response.
           Documents: executor is the default; how to invoke skills.

Every new task
    └─ executor  ← default entry point for everything
           1. Orient  — cf-context + cf-status
           2. Assess  — does this need parallel agents? (almost never)
           3. Plan    — 2–4 lines for non-trivial tasks
           4. Execute — full tool access; load specialists inline as needed
           5. Verify  — run tests, check output, report with evidence

           Inline specialist loading (examples):
               Skill("rust-expert")          → apply patterns in this conversation
               Skill("systematic-debugging") → apply in this conversation
               Skill("docs-agent")           → look up and continue

           ┊
           ┊  escalate only when genuinely parallel work is needed
           ┊
           ▼

manager  ← multi-agent coordinator
    Phase 1 — Plan
        Read relevant REGION.md files (coding, planning, research)
        Ask three planning questions; load advisors if non-obvious:
            design-advisor       "does this need brainstorming or a spec first?"
            git-advisor          "what git strategy: worktrees, branches, PRs?"
            coordination-advisor "parallel vs sequential? dependency graph?"
        Confirm plan with user before executing.

    Phase 2 — Execute
        Parallel work    → Agent tool (multiple calls in one message)
        Sequential+gates → subagent-driven-development
        Single domain    → individual specialist subagent
```

---

## Layer by layer

### using-claudefiles — session-start enforcement

**What it does:** Fires at session start via the system-reminder mechanism. Establishes
skill-checking as a requirement before any response. Documents the executor-first routing
principle and how skills are invoked via the Skill tool.

**Why it exists:** Without session-start enforcement the skill system is opt-in —
skills only run when explicitly directed. The most powerful skills (systematic-debugging,
tdd, brainstorming) are also the ones most likely to be skipped under time pressure.
Session-start enforcement makes the discipline automatic and consistent.

**Why it needs to be short:** using-claudefiles loads on every session. Every token it
consumes is overhead paid on every conversation. It is kept under 300 tokens to minimise
this cost while still establishing the key rules.

**Limitation:** Depends on the system-reminder mechanism loading correctly. If the
session context is compressed heavily or the skill file is missing, the enforcement layer
fails silently — the system degrades to ad-hoc behavior without any warning or indicator.

---

### executor — single-agent default

**What it does:** The entry point for every new task. Orients with cf-context and
cf-status, assesses whether the task genuinely needs parallel agents (high bar),
plans briefly for non-trivial work, executes with full tool access, and verifies
before reporting completion. Loads specialist skills inline via the Skill tool
rather than dispatching them as subagents.

**Why it's the default:** A single agent with full session context outperforms a
coordinated team for the vast majority of tasks. Parallelism has real overhead:
each agent must be briefed from scratch, their outputs must be manually synthesised,
and conflicts resolved. For anything that can be done sequentially, executor avoids
all of that overhead. Most work that feels "complex" is actually just deep — and
depth is handled better by one agent with full context than by several agents with
split context.

**Why specialists load inline, not as subagents:** Subagents lose session state.
They start with only what you put in their prompt. An inline Skill load brings the
skill's patterns into the existing conversation, where executor already knows the
task, the constraints, what's been tried, and what the user cares about. That context
is irreplaceable. Subagent dispatch is the right choice when you want fresh context
(parallel isolation); inline is the right choice when you want to extend existing
context (specialist knowledge).

**Why the Iron Laws:** Executor has two hard rules: "orient before acting" and
"verify before reporting completion." Both exist because the failure modes are
predictable and expensive. Without explicit enforcement:
- "The task is obvious" skips orientation → executor acts on wrong assumptions
  about the codebase or git state.
- "The code is clearly correct" skips verification → bugs ship.

Iron Laws close these loopholes by naming them. A rule that says "skip only if the
tools aren't installed" removes the rationalization surface entirely.

**Limitation:** One context window has limits. Very large tasks (20+ independent
subtasks across genuinely unrelated domains) will see context degradation. This is
when manager is appropriate — but it is a high bar. Sequential complexity, deep
domain work, and multi-file changes across one codebase all stay in executor.

---

### manager — multi-agent coordinator

**What it does:** Runs a planning phase (reading REGION.md files, asking three
planning questions inline, loading relevant advisors), confirms the plan with the
user, then dispatches agents in the execution phase.

**Why planning comes first:** Agent dispatch is expensive to undo. Once agents are
running, context is split and outputs are accumulating. Structural problems in the
plan — wrong agent boundaries, shared state conflicts, missing dependencies —
compound rather than resolve once execution starts. Planning upfront, with explicit
user confirmation, means structural problems get caught before dispatch.

**Why the high escalation bar:** The coordination overhead of multi-agent work is
real. Each agent must be briefed from scratch, their outputs must be synthesised
manually, and conflicts resolved with judgment. For work that can be done sequentially
in one context, manager adds cost without benefit. The bar is: genuinely parallel
work across separate domains, or scale large enough to actually degrade a single
context. Everything else stays in executor.

**Limitation:** Manager cannot automatically merge agent outputs. When parallel
agents return, their results must be synthesised manually — checking for conflicts,
running a full test suite, resolving any divergence. The quality of synthesis
depends directly on how well agent scopes were isolated during planning. Poorly
isolated scopes produce conflicts that are expensive to untangle.

---

### The three advisors — focused planning consultants

| Advisor | Single mandate |
|---------|---------------|
| `design-advisor` | Does this need brainstorming or a written spec before implementation begins? |
| `git-advisor` | What git strategy fits: isolation level, branching, PRs, commit structure? |
| `coordination-advisor` | Parallel vs sequential? Dependency graph? Team composition? Agent boundaries? |

**Why three narrow advisors, not one generalist:**

A generalist advisor (the prior `manager-advisor`) must split attention across three
domains simultaneously. Each domain — design decisions, git strategy, agent coordination
— has enough depth to fill a full planning conversation. Asking one advisor to cover
all three produces shallower output on each dimension.

Role-priming research consistently shows that agents given a single, specific mandate
produce deeper, more reliable analysis than agents asked to cover multiple domains.
This is the mixture-of-experts principle applied to planning: specialists outperform
generalists when each specialist is held to a single question.

Each advisor also has a narrower failure mode. If design-advisor misses something, it
only affects the design/spec decision. With a generalist, a gap in one area contaminates
the whole advisory output.

**Why they load inline, not as subagents:** Planning requires the full context of
the task — the user's description, constraints, REGION.md contents, any prior
conversation. Dispatching as a subagent loses all of that. Loading inline keeps the
advisor in the same conversation where the planning is happening, with access to
everything manager has already read and considered.

**Why they're optional, not always-on:** Not every planning question is non-obvious.
If the git strategy is clearly "commit directly to main," loading git-advisor adds
tokens without adding insight. The advisors exist for genuinely uncertain decisions.
Loading them when the answer is already clear is overhead with no return.

**Limitation:** The advisors are load-on-demand. Manager must exercise judgment about
when a decision is non-obvious enough to warrant consulting one. If manager answers
a planning question inline when it's actually complex, the relevant advisor is never
loaded. There's no automatic trigger or quality gate — it relies on manager's
self-assessment of its own uncertainty.

---

## What the system doesn't do

**No automated agent output merging.** Parallel agents return independently. Their
outputs must be synthesised manually — reading summaries, checking for conflicts,
running tests, resolving any divergence. The system provides no automated merge,
diff, or conflict detection.

**No automatic re-routing.** If executor discovers mid-task that manager would have
been better, there's no automatic handoff. The conversation must be restarted with
manager explicitly. Mid-task escalation is possible but requires user involvement.

**No skill quality testing.** cf-check verifies that REGION.md entries exist for
all leaf skills, but it cannot verify that a skill's content is accurate, current,
or well-calibrated. Skills can drift from actual usage patterns without any automated
signal.

**No advisor quality gates.** Advisors give recommendations; manager decides.
A good recommendation can still be ignored or misapplied. The advisors validate
their reasoning within their narrow domain — they do not validate the final plan.

**Context pressure is invisible.** When executor loads multiple specialist skills
inline during a long session, context fills gradually. The system does not track
this, warn when context is getting tight, or suggest when to start a fresh session.
On tasks that chain many specialist skills across a long conversation, monitor for
context pressure manually.

**using-claudefiles enforcement is passive.** The skill establishes rules and
documents them. It does not actively interrupt or block non-compliant behavior —
enforcement depends on the rules being read and internalized at session start.
