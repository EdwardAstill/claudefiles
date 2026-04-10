# Orchestration Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `subagent-driven-development` (recommended) or `executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace simple-orchestrator + complex-orchestrator with a 5-component system (task-analyser → cheapskill / superskill / manager) plus three consultant skills and four regional docs.

**Architecture:** task-analyser is the always-on entry point that decomposes tasks and routes by complexity. cheapskill/superskill handle simple and medium tasks directly. manager runs a planning phase (reads regional docs, consults advisor skills) then dispatches specialist skills as subagents for difficult tasks.

**Tech Stack:** Bash skill files (SKILL.md with YAML frontmatter + markdown body), bash for cf-check update.

**Spec:** `docs/superpowers/specs/2026-04-10-orchestration-redesign-design.md`

---

## File Map

**Create:**
```
dev-suite/management/orchestration/task-analyser/SKILL.md
dev-suite/management/orchestration/cheapskill/SKILL.md
dev-suite/management/orchestration/superskill/SKILL.md
dev-suite/management/orchestration/manager/SKILL.md
dev-suite/management/consultants/orchestration-consultant/SKILL.md
dev-suite/management/consultants/version-control-consultant/SKILL.md
dev-suite/management/consultants/planning-consultant/SKILL.md
dev-suite/management/REGION.md
dev-suite/planning/REGION.md
dev-suite/coding/REGION.md
dev-suite/research/REGION.md
```

**Modify:**
```
manifest.toml                                 — add 7 new skills, remove 2 old
dev-suite/management/SKILL.md                 — update orchestration table
CLAUDE.md                                     — update all references to old system
bin/cf-check                                  — check REGION.md instead of registry.md
```

**Delete:**
```
dev-suite/management/orchestration/simple-orchestrator/   (directory)
dev-suite/management/orchestration/complex-orchestrator/  (directory)
dev-suite/registry.md
```

---

## Task 1: Create task-analyser

**Files:**
- Create: `dev-suite/management/orchestration/task-analyser/SKILL.md`

- [ ] **Step 1: Create the skill file**

```bash
mkdir -p dev-suite/management/orchestration/task-analyser
```

Write `dev-suite/management/orchestration/task-analyser/SKILL.md`:

```markdown
---
name: task-analyser
description: >
  Always-on entry point. Activates at the start of every task before any other skill acts.
  Decomposes the task into subtasks, scores complexity across scope/domain/coordination,
  then routes to cheapskill (simple: 1-2 subtasks, single domain, no coordination),
  superskill (medium: 3-6 subtasks, manageable solo), or manager (difficult: 7+ subtasks,
  multiple domains, or parallel/team coordination needed). Use at the start of every task.
---

# Task Analyser

Always-on triage layer. Decomposes every incoming task, assesses complexity, and routes to
the right execution path. Nothing else runs until task-analyser has decided where to send it.

## Step 1: Decompose

Break the task into concrete subtasks. Be specific — each subtask should be a discrete unit
of work with a clear output.

## Step 2: Score complexity

Score across three signals:

| Signal | Simple | Medium | Difficult |
|--------|--------|--------|-----------|
| Subtask count | 1–2 | 3–6 | 7+ |
| Domain spread | Single | Single, some unknowns | Multiple domains |
| Coordination needed | None | None | Parallel / team |

Any signal hitting **Difficult** → manager.
All signals **Simple** → cheapskill.
Otherwise → superskill.

**When in doubt, route to the more capable path.** Routing to superskill instead of cheapskill
costs a few extra tokens. Routing to cheapskill when manager was needed wastes the whole task.

## Step 3: Gather codebase context

```bash
cf-context   # project fingerprint: name, language, structure
cf-status    # git state: branch, recent commits, uncommitted changes
```

If neither tool is available, skip this step.

## Step 4: Route with context

Announce the routing decision:

```
Routing to [cheapskill | superskill | manager]
Reason: [which signal(s) triggered this, subtask count: N]
Subtasks:
  1. [subtask]
  2. [subtask]
  ...
```

Then invoke the target skill with:
- **cheapskill:** task text + subtask list
- **superskill:** task text + subtasks + cf-context/cf-status output
- **manager:** task text + subtasks + which regions are involved + cf-context/cf-status output
```

- [ ] **Step 2: Verify frontmatter**

```bash
awk '/^name:/ { gsub(/^name: */, ""); print; exit }' dev-suite/management/orchestration/task-analyser/SKILL.md
```

Expected output: `task-analyser`

- [ ] **Step 3: Commit**

```bash
git add dev-suite/management/orchestration/task-analyser/SKILL.md
git commit -m "feat: add task-analyser — always-on entry point replacing simple-orchestrator"
```

---

## Task 2: Create cheapskill

**Files:**
- Create: `dev-suite/management/orchestration/cheapskill/SKILL.md`

- [ ] **Step 1: Create the skill file**

```bash
mkdir -p dev-suite/management/orchestration/cheapskill
```

Write `dev-suite/management/orchestration/cheapskill/SKILL.md`:

```markdown
---
name: cheapskill
description: >
  Token-minimal execution path for simple tasks. Invoked by task-analyser when all
  complexity signals are Simple: 1-2 subtasks, single domain, no coordination needed.
  Uses the cheapest/fastest available model (haiku or equivalent). No planning overhead,
  no review steps, no subagents. Direct execution only.
---

# Cheapskill

Fast, token-minimal execution for simple, well-defined tasks.

**Model:** Use the cheapest/fastest available model (haiku or equivalent).

## Behaviour

Receives from task-analyser:
- Task text
- Subtask list (1–2 items)

Execute directly:
1. Work through each subtask in sequence
2. No planning phase
3. No review steps
4. No subagents

Return the result.

## Constraints

- Do not invoke other skills
- Do not dispatch subagents
- Do not ask the user for confirmation unless the task is genuinely ambiguous
- If the task turns out to be more complex than routed, report back — do not expand scope
```

- [ ] **Step 2: Verify frontmatter**

```bash
awk '/^name:/ { gsub(/^name: */, ""); print; exit }' dev-suite/management/orchestration/cheapskill/SKILL.md
```

Expected output: `cheapskill`

- [ ] **Step 3: Commit**

```bash
git add dev-suite/management/orchestration/cheapskill/SKILL.md
git commit -m "feat: add cheapskill — token-minimal path for simple tasks"
```

---

## Task 3: Create superskill

**Files:**
- Create: `dev-suite/management/orchestration/superskill/SKILL.md`

- [ ] **Step 1: Create the skill file**

```bash
mkdir -p dev-suite/management/orchestration/superskill
```

Write `dev-suite/management/orchestration/superskill/SKILL.md`:

```markdown
---
name: superskill
description: >
  Capable general agent for medium-complexity tasks. Invoked by task-analyser when
  complexity is medium: 3-6 subtasks, single domain with some unknowns, no parallel
  coordination needed. Full tool access. Self-directed breakdown, tests its own solution,
  asks user when genuinely stuck. Absorbs specialist skills inline — does not invoke
  git-expert, python-expert, rust-expert etc. as subagents.
---

# Superskill

Capable general agent for medium-complexity work. Handles the task end-to-end with full
tool access and self-directed execution.

## Behaviour

Receives from task-analyser:
- Task text + subtask list
- Codebase context (cf-context + cf-status output)

Execute:
1. Review the subtask breakdown — break down further if needed
2. Work through each subtask with full tool access
3. Test the solution (run tests, verify output, check for regressions)
4. Ask the user only when genuinely stuck at a decision point
5. Report completion with a summary of what was done

## Tool access

Use whatever tools the task requires: Read, Write, Edit, Bash, Glob, Grep, Agent,
WebSearch, WebFetch.

## Absorbing specialist skills

Do not invoke specialist skills (`git-expert`, `python-expert`, `rust-expert`,
`typescript-expert`, `api-architect`, etc.) as separate subagents for medium tasks.
Handle domain work inline using your general knowledge and the available tools.

Specialist skills exist for the manager to dispatch in difficult tasks where deep
domain expertise is needed in an isolated subagent.

## When to ask the user

Ask when:
- A decision point has meaningful trade-offs and the user's preference matters
- You have hit a genuine blocker that requires information only the user has

Do not ask when:
- The correct path is clear from context
- You can make a reasonable assumption and note it in your response
```

- [ ] **Step 2: Verify frontmatter**

```bash
awk '/^name:/ { gsub(/^name: */, ""); print; exit }' dev-suite/management/orchestration/superskill/SKILL.md
```

Expected output: `superskill`

- [ ] **Step 3: Commit**

```bash
git add dev-suite/management/orchestration/superskill/SKILL.md
git commit -m "feat: add superskill — general agent for medium-complexity tasks"
```

---

## Task 4: Create manager

**Files:**
- Create: `dev-suite/management/orchestration/manager/SKILL.md`

- [ ] **Step 1: Create the skill file**

```bash
mkdir -p dev-suite/management/orchestration/manager
```

Write `dev-suite/management/orchestration/manager/SKILL.md`:

```markdown
---
name: manager
description: >
  Full coordinator for difficult tasks: 7+ subtasks, multiple domains, or parallel/team
  coordination needed. Invoked by task-analyser. Runs a planning phase — reads regional
  docs, then consults planning-consultant, version-control-consultant, and
  orchestration-consultant sequentially in the same conversation — then an execution phase
  dispatching specialist skills as subagents. Replaces complex-orchestrator.
---

# Manager

Coordinator for difficult tasks. Two phases: planning (understand the full picture, consult
domain advisors) then execution (dispatch the right skills in the right order).

**Model:** Use the most capable available model (Opus or equivalent).

## Planning phase

### 1. Read regional docs

Task-analyser identified which regions are involved. Read those REGION.md files:

```bash
# Example — if coding and planning are involved:
cat dev-suite/coding/REGION.md
cat dev-suite/planning/REGION.md
```

Available regions: `management`, `planning`, `coding`, `research`.

Build an initial task breakdown: which skills to use, rough sequence, what each produces.

### 2. Consult

Load consultant skills sequentially in this order. For each, present the **full current plan**
plus where you think their input will be most useful — but they can advise on anything.

**Order:**
1. `planning-consultant` — flags whether a brainstorm/spec phase is needed before execution
2. `version-control-consultant` — advises on git workflow (worktrees, branches, PRs)
3. `orchestration-consultant` — advises on parallel vs sequential, team structures

After each consultant responds, incorporate their advice and update the plan before moving
to the next consultant.

Skip a consultant if their domain clearly does not apply to this task.

### 3. Finalise and confirm

Present the final execution plan to the user:
- Which skills run, in what order (or in parallel)
- What each step produces
- How outputs feed into subsequent steps

Wait for user confirmation before executing.

## Execution phase

Dispatch specialist skills as subagents per the confirmed plan.

- Use `dispatching-parallel-agents` for tasks that can run concurrently
- Use `subagent-driven-development` for sequential implementation tasks with review gates
- Dispatch individual specialist skills as subagents for focused domain work

## Consultant vs specialist — the boundary

| | Consultants | Specialists |
|---|---|---|
| **Phase** | Planning only | Execution only |
| **How** | Loaded into this conversation | Dispatched as subagents |
| **Purpose** | Advise on structure | Do the work |

Never dispatch a consultant as a subagent. Never load a specialist for planning advice.
```

- [ ] **Step 2: Verify frontmatter**

```bash
awk '/^name:/ { gsub(/^name: */, ""); print; exit }' dev-suite/management/orchestration/manager/SKILL.md
```

Expected output: `manager`

- [ ] **Step 3: Commit**

```bash
git add dev-suite/management/orchestration/manager/SKILL.md
git commit -m "feat: add manager — coordinator for difficult tasks replacing complex-orchestrator"
```

---

## Task 5: Create orchestration-consultant

**Files:**
- Create: `dev-suite/management/consultants/orchestration-consultant/SKILL.md`

- [ ] **Step 1: Create the skill file**

```bash
mkdir -p dev-suite/management/consultants/orchestration-consultant
```

Write `dev-suite/management/consultants/orchestration-consultant/SKILL.md`:

```markdown
---
name: orchestration-consultant
description: >
  Planning-phase advisor to the manager on agent coordination patterns. Loaded into the
  same conversation (not dispatched as a subagent). Reviews the manager's full plan and
  advises on parallel vs sequential execution, team structures, and subagent dispatch
  patterns. Knows dispatching-parallel-agents and subagent-driven-development. Third
  consultant loaded, after planning-consultant and version-control-consultant.
---

# Orchestration Consultant

Advisor to the manager on agent coordination patterns.

## Role

The manager loads you during its planning phase (third, after planning-consultant and
version-control-consultant). The manager will give you the full current plan and flag the
points where your input is most needed — but you can advise on any part of the plan.

## What you advise on

**Parallel execution:**
- Which subtasks have no shared state and can safely run concurrently
- Which subtasks have data dependencies and must run sequentially
- Where parallelism saves meaningful time vs adds complexity

**Team structures:**
- When a subtask is complex enough to warrant multiple agents working together
- How to split work between a lead agent and supporting agents

**Dispatch patterns:**

| Pattern | Use when |
|---------|----------|
| `dispatching-parallel-agents` | Multiple independent tasks with no ordering constraints |
| `subagent-driven-development` | Sequential tasks where each needs a fresh context + review gate |
| Inline execution (no subagents) | Simple coordination the manager can handle directly |

## How to respond

Comment on the flagged points first, then anything else you spot in the plan.
Be specific: name the subtasks, explain the dependency or opportunity, give a concrete
recommendation. Don't describe patterns in the abstract — apply them to this plan.
```

- [ ] **Step 2: Verify frontmatter**

```bash
awk '/^name:/ { gsub(/^name: */, ""); print; exit }' dev-suite/management/consultants/orchestration-consultant/SKILL.md
```

Expected output: `orchestration-consultant`

- [ ] **Step 3: Commit**

```bash
git add dev-suite/management/consultants/orchestration-consultant/SKILL.md
git commit -m "feat: add orchestration-consultant — agent coordination advisor for manager"
```

---

## Task 6: Create version-control-consultant

**Files:**
- Create: `dev-suite/management/consultants/version-control-consultant/SKILL.md`

- [ ] **Step 1: Create the skill file**

```bash
mkdir -p dev-suite/management/consultants/version-control-consultant
```

Write `dev-suite/management/consultants/version-control-consultant/SKILL.md`:

```markdown
---
name: version-control-consultant
description: >
  Planning-phase advisor to the manager on git workflow — worktrees, branches, PRs, and
  commit structure. Loaded into the same conversation (not dispatched as a subagent).
  Reviews the manager's full plan and advises on when isolated worktrees are appropriate,
  when a branch suffices, PR strategy, and commit granularity. Knows git-worktree-workflow,
  git-expert, github-expert. Second consultant loaded, after planning-consultant.
---

# Version Control Consultant

Advisor to the manager on git workflow.

## Role

The manager loads you during its planning phase (second, after planning-consultant). The
manager will give you the full current plan and flag the points where your input is most
needed — but you can advise on any part of the plan.

## What you advise on

**Worktrees — use `git-worktree-workflow` when:**
- The work is a discrete feature that will run alongside other ongoing work
- Implementation risk could destabilise the main branch mid-way
- The task involves multiple commits over an extended period

**Skip worktrees when:**
- It is a small fix, docs change, or single-file edit
- The task will be completed in one sitting with no parallel work

**Branches:**
- When a named branch (without a full worktree) is the right isolation level
- Typical for short-lived work with no parallelism concerns

**PRs:**
- When the work warrants review before merging (use `github-expert` for PR creation)
- Direct commit to main is fine for small, safe changes on personal repos

**Commit structure:**
- One logical change per commit
- Frequent small commits during implementation; consider squashing before PR

## Skills I know

| Skill | Use when |
|-------|----------|
| `git-worktree-workflow` | Feature work needing isolation; call at plan start AND end |
| `git-expert` | Complex git operations: history rewrite, conflict resolution, bisect |
| `github-expert` | PR creation, review, GitHub Actions, issue management |

## How to respond

Comment on the flagged points first, then anything else you spot.
Give concrete recommendations: name the skill, say when in the plan to invoke it.
```

- [ ] **Step 2: Verify frontmatter**

```bash
awk '/^name:/ { gsub(/^name: */, ""); print; exit }' dev-suite/management/consultants/version-control-consultant/SKILL.md
```

Expected output: `version-control-consultant`

- [ ] **Step 3: Commit**

```bash
git add dev-suite/management/consultants/version-control-consultant/SKILL.md
git commit -m "feat: add version-control-consultant — git workflow advisor for manager"
```

---

## Task 7: Create planning-consultant

**Files:**
- Create: `dev-suite/management/consultants/planning-consultant/SKILL.md`

- [ ] **Step 1: Create the skill file**

```bash
mkdir -p dev-suite/management/consultants/planning-consultant
```

Write `dev-suite/management/consultants/planning-consultant/SKILL.md`:

```markdown
---
name: planning-consultant
description: >
  Planning-phase advisor to the manager on design/spec/plan cycles. Always the first
  consultant loaded. Reviews the manager's full plan and flags when a task needs a
  brainstorm or spec phase before implementation begins. Advises on execution approach:
  subagent-driven-development vs executing-plans vs inline. Knows brainstorming,
  writing-plans, executing-plans, subagent-driven-development.
---

# Planning Consultant

Advisor to the manager on when and how to use design and planning workflows.

## Role

The manager loads you **first** in the planning phase (before version-control-consultant and
orchestration-consultant). The manager will give you the full current plan and flag the
points where your input is most needed — but you can advise on any part.

Your most important job: flag when the task should go through a design phase before
implementation begins. Catching this early is far cheaper than discovering it mid-execution.

## What you advise on

**When to brainstorm first:**
- The task involves design decisions that haven't been made yet
- The task is building something new with unclear requirements
- The user's intent is ambiguous or underspecified
- → Recommend invoking `brainstorming` before the manager proceeds with execution

**When to write a detailed plan first:**
- The implementation is complex enough that each subtask needs step-by-step instructions
- Multiple agents will execute the work and need a shared reference document
- → Recommend invoking `writing-plans` to produce a detailed plan before dispatch

**Execution approach:**

| Approach | Use when |
|----------|----------|
| `subagent-driven-development` | Sequential tasks in this session, each needing fresh context + review |
| `executing-plans` | Handing off a plan to a parallel session |
| Inline | Manager executes directly without subagents |

## Skills I know

| Skill | Use when |
|-------|----------|
| `brainstorming` | Idea → design → spec; use when requirements are unclear |
| `writing-plans` | Spec → detailed step-by-step plan; use before complex multi-agent work |
| `executing-plans` | Execute a plan in a parallel session |
| `subagent-driven-development` | Execute a plan in this session with fresh subagent per task + review |

## How to respond

Comment on the flagged points first, then anything else.
If the task needs brainstorming or a written plan first, say so directly — don't soften it.
The manager's time is better spent catching this now than mid-execution.
```

- [ ] **Step 2: Verify frontmatter**

```bash
awk '/^name:/ { gsub(/^name: */, ""); print; exit }' dev-suite/management/consultants/planning-consultant/SKILL.md
```

Expected output: `planning-consultant`

- [ ] **Step 3: Commit**

```bash
git add dev-suite/management/consultants/planning-consultant/SKILL.md
git commit -m "feat: add planning-consultant — design/spec/plan cycle advisor for manager"
```

---

## Task 8: Create four REGION.md files

**Files:**
- Create: `dev-suite/management/REGION.md`
- Create: `dev-suite/planning/REGION.md`
- Create: `dev-suite/coding/REGION.md`
- Create: `dev-suite/research/REGION.md`

These replace `registry.md`. Each catalogs the skills in that region so the manager can
quickly inventory available tools. Format per spec: `### skill-name` heading + 4 bullet fields.

- [ ] **Step 1: Write dev-suite/management/REGION.md**

```markdown
# Management Region

Skills for orchestration, coordination, and skill system tooling.

---

### task-analyser
- **Purpose:** Always-on entry point — decomposes tasks, scores complexity, routes to cheap/super/manager
- **Use when:** Start of every task (automatic)
- **Produces:** Routing decision + subtask breakdown passed to cheapskill/superskill/manager
- **Chains into:** cheapskill, superskill, manager

### cheapskill
- **Purpose:** Token-minimal direct execution for simple tasks using a cheap/fast model
- **Use when:** Task-analyser routes here — 1-2 subtasks, single domain, no coordination
- **Produces:** Completed task output
- **Chains into:** (terminal)

### superskill
- **Purpose:** Capable general agent for medium-complexity tasks — full tools, self-directed
- **Use when:** Task-analyser routes here — 3-6 subtasks, manageable solo
- **Produces:** Completed task output with self-testing
- **Chains into:** (terminal)

### manager
- **Purpose:** Coordinator for difficult tasks — planning phase + multi-agent execution
- **Use when:** Task-analyser routes here — 7+ subtasks, multiple domains, parallel/team needed
- **Produces:** Executed multi-skill workflow
- **Chains into:** Any specialist skill (via subagent dispatch)

### orchestration-consultant
- **Purpose:** Advises manager on parallel vs sequential execution and team structures
- **Use when:** Manager's planning phase — third consultant loaded
- **Produces:** Coordination recommendations for the plan
- **Chains into:** (planning phase only — no execution chaining)

### version-control-consultant
- **Purpose:** Advises manager on git workflow — worktrees, branches, PRs, commit structure
- **Use when:** Manager's planning phase — second consultant loaded
- **Produces:** Git workflow recommendations for the plan
- **Chains into:** (planning phase only — no execution chaining)

### planning-consultant
- **Purpose:** Advises manager on when to brainstorm/spec/plan before executing
- **Use when:** Manager's planning phase — first consultant loaded
- **Produces:** Planning approach recommendation (brainstorm first? write a plan? execute directly?)
- **Chains into:** brainstorming, writing-plans (if design phase is needed)

### skill-manager
- **Purpose:** View, install, and remove skills across global and project scopes
- **Use when:** User wants to see what skills are installed, install new ones, or remove old ones
- **Produces:** Installed/removed skills; listing of current skill state
- **Chains into:** (terminal)

### writing-skills
- **Purpose:** Create or edit SKILL.md files following the claudefiles format
- **Use when:** User wants to author a new skill or edit an existing one
- **Produces:** New or updated SKILL.md with valid frontmatter and structured body
- **Chains into:** skill-manager (install after writing)

### dispatching-parallel-agents
- **Purpose:** Fire multiple independent Agent subagents simultaneously
- **Use when:** Several tasks with no shared state can run concurrently
- **Produces:** Parallel task outputs
- **Chains into:** (aggregation step after all complete)

### subagent-driven-development
- **Purpose:** Execute an implementation plan task-by-task with fresh subagent + two-stage review per task
- **Use when:** Have an implementation plan; want sequential execution with review gates in this session
- **Produces:** Committed, reviewed implementation
- **Chains into:** git-worktree-workflow (finish), requesting-code-review
```

- [ ] **Step 2: Write dev-suite/planning/REGION.md**

```markdown
# Planning Region

Skills for the design → spec → plan → implement lifecycle.

---

### brainstorming
- **Purpose:** Turn an idea into a fully designed spec through collaborative dialogue
- **Use when:** Have an idea or request — haven't designed it yet; requirements unclear
- **Produces:** Approved design doc saved to docs/superpowers/specs/
- **Chains into:** writing-plans

### writing-plans
- **Purpose:** Turn an approved spec into a detailed step-by-step implementation plan
- **Use when:** Have an approved spec/design — need an implementation plan
- **Produces:** Implementation plan saved to docs/superpowers/plans/
- **Chains into:** subagent-driven-development, executing-plans

### executing-plans
- **Purpose:** Hand off an implementation plan to a fresh parallel session for execution
- **Use when:** Have a plan — want to execute it in a new session without carrying current context
- **Produces:** Executed plan (in the new session)
- **Chains into:** (execution in parallel session)
```

- [ ] **Step 3: Write dev-suite/coding/REGION.md**

```markdown
# Coding Region

Skills for implementation, quality, version control, and language-specific work.

---

## Quality

### tdd
- **Purpose:** Test-driven development — write failing test, implement, pass, commit
- **Use when:** Writing new functionality; any implementation task
- **Produces:** Tested, committed implementation
- **Chains into:** verification-before-completion, requesting-code-review

### systematic-debugging
- **Purpose:** Structured bug investigation — reproduce, isolate, fix, verify
- **Use when:** Bug report or unexpected behaviour; test failures
- **Produces:** Root cause identified, fix committed, regression test added
- **Chains into:** verification-before-completion

### verification-before-completion
- **Purpose:** Final check before declaring a task done — tests pass, no regressions
- **Use when:** Before marking any implementation task complete
- **Produces:** Go/no-go signal; failing tests reported
- **Chains into:** (terminal if passing); tdd, systematic-debugging (if failing)

### requesting-code-review
- **Purpose:** Dispatch a code reviewer subagent to review implemented changes
- **Use when:** Implementation complete; want a quality check before merging
- **Produces:** Review findings (approval or issues list)
- **Chains into:** receiving-code-review

### receiving-code-review
- **Purpose:** Process code review feedback — triage, fix, or push back on each issue
- **Use when:** Have code review findings to act on
- **Produces:** Addressed review comments; updated code
- **Chains into:** verification-before-completion, requesting-code-review (re-review)

### simplify
- **Purpose:** Reduce code complexity — remove duplication, dead code, over-engineering
- **Use when:** Code is working but complex; after a large implementation; refactor request
- **Produces:** Simpler code with same behaviour; committed
- **Chains into:** verification-before-completion

---

## Version Control

### git-worktree-workflow
- **Purpose:** Full worktree lifecycle — create isolated workspace, verify baseline, finish with merge/PR/discard
- **Use when:** Starting feature work that needs isolation; completing work in a worktree
- **Produces:** Isolated branch + worktree (setup); merged/PR'd/cleaned work (finish)
- **Chains into:** specialist skill (after setup); git-expert, github-expert (at finish)

### git-expert
- **Purpose:** Deep git operations — complex history, conflict resolution, bisect, reflog
- **Use when:** Git operation beyond everyday commit/push/merge; something went wrong
- **Produces:** Resolved git state; history cleaned; conflict resolved
- **Chains into:** github-expert (if PR needed after)

### github-expert
- **Purpose:** GitHub-specific workflows — PRs, issues, Actions, branch protection
- **Use when:** Creating or managing PRs; GitHub Actions; repo settings
- **Produces:** PR created/merged; Actions configured; issue managed
- **Chains into:** (terminal)

---

## Architecture

### api-architect
- **Purpose:** Design and review API contracts — REST, GraphQL, RPC; schema design
- **Use when:** Designing a new API or reviewing an existing one for consistency/correctness
- **Produces:** API design document or review findings
- **Chains into:** tdd (implement the designed API)

---

## Languages

### python-expert
- **Purpose:** Python implementation with type safety — pyright LSP, uv, ruff, pytest
- **Use when:** Writing, debugging, or reviewing Python code
- **Produces:** Type-checked, ruff-clean, tested Python code
- **Chains into:** tdd, systematic-debugging, verification-before-completion

### typescript-expert
- **Purpose:** TypeScript/JS implementation — typescript-language-server LSP, bun, biome
- **Use when:** Writing, debugging, or reviewing TypeScript or JavaScript code
- **Produces:** Strictly typed, biome-clean, tested TypeScript code
- **Chains into:** tdd, systematic-debugging, verification-before-completion

### rust-expert
- **Purpose:** Rust implementation — rust-analyzer LSP, cargo, clippy, rustfmt
- **Use when:** Writing, debugging, or reviewing Rust code
- **Produces:** Clippy-clean, rustfmt-formatted, tested Rust code
- **Chains into:** tdd, systematic-debugging, verification-before-completion

### typst-expert
- **Purpose:** Typst document authoring — tinymist LSP, typst compile/watch
- **Use when:** Writing or debugging Typst documents
- **Produces:** Compiling .typ document with correct output
- **Chains into:** (terminal)
```

- [ ] **Step 4: Write dev-suite/research/REGION.md**

```markdown
# Research Region

Skills for documentation lookup and research.

---

### docs-agent
- **Purpose:** Fetch current documentation for libraries, frameworks, SDKs, APIs, and CLI tools
- **Use when:** Need accurate API signatures, config options, or working examples for a specific library
- **Produces:** API reference, working example, source URL, version note
- **Chains into:** api-architect (feeds reference into design), python-expert / typescript-expert / rust-expert

### research-agent
- **Purpose:** General research and critical analysis — expert consensus, trade-offs, pitfalls
- **Use when:** Evaluating an approach, understanding risks, or finding expert consensus before committing
- **Produces:** Structured report: consensus, nuances, pitfalls, contradictions, recommended direction
- **Chains into:** api-architect (informs design), brainstorming (informs spec)
```

- [ ] **Step 5: Verify all four files exist**

```bash
ls dev-suite/management/REGION.md dev-suite/planning/REGION.md dev-suite/coding/REGION.md dev-suite/research/REGION.md
```

Expected: all four paths listed with no errors.

- [ ] **Step 6: Commit**

```bash
git add dev-suite/management/REGION.md dev-suite/planning/REGION.md dev-suite/coding/REGION.md dev-suite/research/REGION.md
git commit -m "feat: add regional docs — replace registry.md with per-category REGION.md files"
```

---

## Task 9: Update manifest.toml

**Files:**
- Modify: `manifest.toml`

Add 7 new skill entries and remove the 2 old orchestration entries.

- [ ] **Step 1: Add new skill entries**

Open `manifest.toml`. After the existing `[skills.subagent-driven-development]` entry, add:

```toml
[skills.task-analyser]
tools = ["Bash", "Read"]

[skills.cheapskill]
tools = []

[skills.superskill]
tools = ["Bash", "Read", "Write", "Edit", "Glob", "Grep", "Agent", "WebSearch", "WebFetch"]

[skills.manager]
tools = ["Bash", "Read", "Agent"]

[skills.orchestration-consultant]
tools = []

[skills.version-control-consultant]
tools = []

[skills.planning-consultant]
tools = []
```

- [ ] **Step 2: Remove old entries**

Remove these two blocks from manifest.toml:

```toml
[skills.simple-orchestrator]
# Reads only in-context frontmatter — no additional tools needed
tools = []

[skills.complex-orchestrator]
# Reads registry.md
tools = ["Read"]
```

- [ ] **Step 3: Verify**

```bash
grep -c "^\[skills\." manifest.toml
```

Expected: 30 (was 25 + 7 new - 2 removed = 30)

```bash
grep "simple-orchestrator\|complex-orchestrator" manifest.toml
```

Expected: no output.

- [ ] **Step 4: Commit**

```bash
git add manifest.toml
git commit -m "feat: update manifest.toml — add 7 new orchestration skills, remove old 2"
```

---

## Task 10: Update management SKILL.md dispatcher

**Files:**
- Modify: `dev-suite/management/SKILL.md`

Replace the orchestration table and update the description to reference the new skills.

- [ ] **Step 1: Rewrite the file**

Write `dev-suite/management/SKILL.md`:

```markdown
---
name: management
description: >
  Category dispatcher for orchestration and skill system tooling. Orchestration is
  automatic — task-analyser activates at the start of every task and routes to
  cheapskill (simple), superskill (medium), or manager (difficult). For parallel
  independent tasks use dispatching-parallel-agents. For sequential plan execution
  with review gates use subagent-driven-development. For skill installation and
  authoring use the meta skills.
---

# Management

Routes to orchestration skills or skill system meta tooling.

## Orchestration

Orchestration is automatic. task-analyser runs at the start of every task.

| Skill | Role |
|-------|------|
| `task-analyser` | Always-on entry point — decomposes and routes |
| `cheapskill` | Simple tasks — haiku model, direct execution |
| `superskill` | Medium tasks — Sonnet, capable general agent |
| `manager` | Difficult tasks — Opus, planning + multi-agent execution |

## Execution helpers

| Skill | Use when |
|-------|----------|
| `subagent-driven-development` | Execute a plan in this session with fresh subagent + review per task |
| `dispatching-parallel-agents` | Fire multiple independent tasks simultaneously |

## Manager's planning consultants

Loaded by manager during its planning phase (not invoked directly by users):

| Consultant | Advises on |
|------------|------------|
| `planning-consultant` | When to brainstorm/spec/plan before executing |
| `version-control-consultant` | Git workflow — worktrees, branches, PRs |
| `orchestration-consultant` | Parallel vs sequential, team structures |

## Meta skills

| Skill | Use when |
|-------|----------|
| `skill-manager` | Viewing, installing, or removing skills across scopes |
| `writing-skills` | Creating or editing a skill |
```

- [ ] **Step 2: Verify the description field is present and valid**

```bash
awk '/^name:/ { gsub(/^name: */, ""); print; exit }' dev-suite/management/SKILL.md
```

Expected output: `management`

- [ ] **Step 3: Commit**

```bash
git add dev-suite/management/SKILL.md
git commit -m "feat: update management dispatcher — reference new orchestration skills"
```

---

## Task 11: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

Update all references to the old system: simple-orchestrator, complex-orchestrator, registry.md.

- [ ] **Step 1: Replace the orchestration description in Key Facts**

Find this line (around line 20):
```
- **Registry lives at** `dev-suite/registry.md` — the complex-orchestrator reads this
```

Replace with:
```
- **Regional docs live at** `dev-suite/<category>/REGION.md` — the manager reads these during planning
```

- [ ] **Step 2: Replace the registry sync section**

Find the Registry Sync Rule section:
```
**Any time a skill's inputs, outputs, or chain targets change, update `dev-suite/registry.md`.**

The registry is the contract between skills. If it drifts from reality, complex-orchestrator
will misplan. Keep it accurate.

Run `cf-check` before committing any changes to `dev-suite/` to verify all leaf skills have
registry entries.
```

Replace with:
```
**Any time a skill's inputs, outputs, or chain targets change, update its category's `REGION.md`.**

Regional docs are the contract between skills and the manager. If they drift from reality, the
manager will misplan. Keep them accurate.

Run `cf-check` before committing any changes to `dev-suite/` to verify all leaf skills have
entries in their category's REGION.md.
```

- [ ] **Step 3: Replace the registry entry in the new-skill checklist**

Find:
```
- [ ] Add entry to `dev-suite/registry.md` (inputs, outputs, chains)
```

Replace with:
```
- [ ] Add entry to `dev-suite/<category>/REGION.md` (purpose, use when, produces, chains into)
```

- [ ] **Step 4: Replace Architecture Notes section**

Find:
```
**Two-tier orchestration:**
- `simple-orchestrator` — reads frontmatter only (already in context). Assesses complexity, routes or escalates. No file I/O.
- `complex-orchestrator` — reads `registry.md`. Plans multi-skill workflows. Only invoked by simple-orchestrator.
```

Replace with:
```
**Three-path orchestration:**
- `task-analyser` — always-on entry point. Decomposes task, scores complexity, routes to cheapskill/superskill/manager.
- `cheapskill` — haiku model, direct execution, no overhead. For simple tasks.
- `superskill` — Sonnet, full tools, self-directed. For medium tasks. Absorbs specialist skills inline.
- `manager` — Opus, planning phase (reads REGION.md files + consults advisor skills) then execution phase. For difficult tasks.
```

- [ ] **Step 5: Update remaining simple-orchestrator reference in Slash Commands section**

Find:
```
the git-expert skill immediately without waiting for simple-orchestrator to route it.
```

Replace with:
```
the git-expert skill immediately without waiting for task-analyser to route it.
```

- [ ] **Step 6: Verify no old references remain**

```bash
grep -n "simple-orchestrator\|complex-orchestrator\|registry\.md" CLAUDE.md
```

Expected: no output.

- [ ] **Step 7: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md — replace old orchestration references with new system"
```

---

## Task 12: Update cf-check

**Files:**
- Modify: `bin/cf-check`

Change cf-check to verify each leaf skill has a `### skill-name` entry in its category's
REGION.md, instead of a `## skill-name` entry in the global registry.md.

The category is derived from the skill's path: `dev-suite/CATEGORY/...`

- [ ] **Step 1: Rewrite bin/cf-check**

Write `bin/cf-check`:

```bash
#!/usr/bin/env bash
# cf-check — verify all leaf skills in dev-suite have an entry in their category's REGION.md
#
# Usage:
#   cf-check           # check from current directory or installed location
#   cf-check --verbose # show passing entries too

set -euo pipefail

VERBOSE=false
for arg in "$@"; do
    [[ "$arg" == "--verbose" ]] && VERBOSE=true
done

# Locate dev-suite
SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
SUITE="$SCRIPT_DIR/../dev-suite"

if [[ ! -d "$SUITE" ]]; then
    echo "Error: dev-suite not found at $SUITE" >&2
    exit 1
fi

bold=""  green=""  red=""  reset=""
if [[ -t 1 ]]; then
    bold="\033[1m"; green="\033[0;32m"; red="\033[0;31m"; reset="\033[0m"
fi

missing=()
found=()

while IFS= read -r skill_md; do
    # Determine if this is a leaf skill: its directory has no child SKILL.md files
    skill_dir="$(dirname "$skill_md")"
    child_skills="$(find "$skill_dir" -mindepth 2 -name "SKILL.md" 2>/dev/null | head -1)"
    [[ -n "$child_skills" ]] && continue  # dispatcher — skip

    name="$(awk '/^name:/ { gsub(/^name: */, ""); print; exit }' "$skill_md" 2>/dev/null)"
    [[ -z "$name" ]] && continue

    # Derive category from path: dev-suite/CATEGORY/...
    relative="${skill_md#$SUITE/}"
    category="${relative%%/*}"
    region_file="$SUITE/$category/REGION.md"

    if [[ ! -f "$region_file" ]]; then
        missing+=("$name (no REGION.md for category: $category)")
        continue
    fi

    if grep -q "^### $name" "$region_file" 2>/dev/null; then
        found+=("$name")
        $VERBOSE && echo -e "  ${green}✓${reset}  $name"
    else
        missing+=("$name")
    fi
done < <(find "$SUITE" -name "SKILL.md" | sort)

echo ""
if [[ ${#missing[@]} -eq 0 ]]; then
    echo -e "  ${green}✓${reset}  Regional docs in sync — ${#found[@]} skills, all have entries"
    echo ""
    exit 0
else
    echo -e "  ${red}✗${reset}  ${#missing[@]} skill(s) missing from their category REGION.md:"
    for name in "${missing[@]}"; do
        echo "       - $name"
    done
    echo ""
    echo "  Add ### entries to the appropriate dev-suite/<category>/REGION.md file."
    echo ""
    exit 1
fi
```

- [ ] **Step 2: Run cf-check (will fail — new skills not yet in REGION.md, old registry gone)**

This step just confirms the script runs without syntax errors. At this point the new skills
are in REGION.md (Task 8) but the old registry.md still exists. cf-check no longer reads it.

```bash
bash -n bin/cf-check && echo "Syntax OK"
```

Expected: `Syntax OK`

- [ ] **Step 3: Commit**

```bash
git add bin/cf-check
git commit -m "feat: update cf-check — check REGION.md per category instead of registry.md"
```

---

## Task 13: Delete old skills and registry.md

**Files:**
- Delete: `dev-suite/management/orchestration/simple-orchestrator/` (directory)
- Delete: `dev-suite/management/orchestration/complex-orchestrator/` (directory)
- Delete: `dev-suite/registry.md`

- [ ] **Step 1: Remove old orchestration skills**

```bash
git rm -r dev-suite/management/orchestration/simple-orchestrator/
git rm -r dev-suite/management/orchestration/complex-orchestrator/
```

- [ ] **Step 2: Remove registry.md**

```bash
git rm dev-suite/registry.md
```

- [ ] **Step 3: Verify they are gone**

```bash
ls dev-suite/management/orchestration/
```

Expected output: `dispatching-parallel-agents  manager  cheapskill  superskill  task-analyser  subagent-driven-development`
(exact order may vary, but simple-orchestrator and complex-orchestrator must NOT appear)

```bash
ls dev-suite/registry.md 2>&1
```

Expected: `ls: cannot access 'dev-suite/registry.md': No such file or directory`

- [ ] **Step 4: Commit**

```bash
git commit -m "feat: remove simple-orchestrator, complex-orchestrator, registry.md — replaced by new system"
```

---

## Task 14: Final verification

- [ ] **Step 1: Run cf-check verbose**

```bash
bash bin/cf-check --verbose
```

Expected: all leaf skills listed with ✓, "Regional docs in sync" message, exit 0.

If any skills are missing from REGION.md, add `### skill-name` entries before proceeding.

- [ ] **Step 2: Verify no old references remain**

```bash
grep -r "simple-orchestrator\|complex-orchestrator\|registry\.md" dev-suite/ CLAUDE.md manifest.toml --include="*.md" --include="*.toml" 2>/dev/null
```

Expected: no output.

- [ ] **Step 3: Verify all new SKILL.md files have valid frontmatter**

```bash
for f in \
  dev-suite/management/orchestration/task-analyser/SKILL.md \
  dev-suite/management/orchestration/cheapskill/SKILL.md \
  dev-suite/management/orchestration/superskill/SKILL.md \
  dev-suite/management/orchestration/manager/SKILL.md \
  dev-suite/management/consultants/orchestration-consultant/SKILL.md \
  dev-suite/management/consultants/version-control-consultant/SKILL.md \
  dev-suite/management/consultants/planning-consultant/SKILL.md; do
  name="$(awk '/^name:/ { gsub(/^name: */, ""); print; exit }' "$f")"
  echo "$name  ← $f"
done
```

Expected: 7 lines, each showing the skill name followed by its path.

- [ ] **Step 4: Count total SKILL.md files**

```bash
find dev-suite/ -name "SKILL.md" | wc -l
```

Expected: ≥ 32 (was 32 before; +7 new skills - 2 deleted = 37)

- [ ] **Step 5: Final commit if anything was fixed**

```bash
git status
# commit any remaining changes
```
