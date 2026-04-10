# Dev Suite Registry

Read by `complex-orchestrator` to understand skill contracts and plan multi-skill workflows.
Keep this in sync when adding or changing skills. Run `cf-check` to verify sync.

---

## Taxonomy

```
dev-suite/
├── management/           ← orchestration and skill system tooling
│   ├── orchestration/
│   │   ├── simple-orchestrator
│   │   ├── complex-orchestrator
│   │   ├── dispatching-parallel-agents
│   │   └── subagent-driven-development
│   └── meta/
│       ├── skill-manager
│       └── writing-skills
├── planning/             ← design-plan-execute lifecycle
│   ├── brainstorming
│   ├── writing-plans
│   └── executing-plans
├── coding/               ← code writing, review, version control, API design
│   ├── quality/
│   │   ├── tdd
│   │   ├── systematic-debugging
│   │   ├── verification-before-completion
│   │   ├── requesting-code-review
│   │   ├── receiving-code-review
│   │   └── simplify
│   ├── version-control/
│   │   ├── git-expert
│   │   ├── github-expert
│   │   └── git-worktree-workflow
│   └── api/
│       └── api-architect
└── research/             ← technical reference, analysis, trade-offs
    ├── docs-agent
    └── research-agent
```

---

## simple-orchestrator

- **Purpose:** Lightweight triage — assess complexity, route or escalate
- **Triggers when:** Every task begins
- **Inputs:** User task description (from context)
- **Outputs:** Routing decision + context summary (if escalating)
- **Tools required:** None (reads frontmatter already in context)
- **Chains into:** Any specialist skill (direct route) or `complex-orchestrator` (escalation)

---

## complex-orchestrator

- **Purpose:** Full multi-skill planning and coordination
- **Triggers when:** simple-orchestrator escalates a high-complexity task
- **Inputs:** User goal, complexity axes that scored HIGH, known context summary
- **Outputs:** Executed multi-skill plan with collected results
- **Tools required:** Read (reads this registry)
- **Chains into:** All skills (coordinates them)

---

## dispatching-parallel-agents

- **Purpose:** Dispatch multiple agents to work on independent tasks simultaneously
- **Triggers when:** Multiple independent failures or tasks that can run concurrently without shared state
- **Inputs:** List of independent problem domains with scopes and constraints
- **Outputs:** Summaries from each agent; integrated fixes
- **Tools required:** Agent
- **Chains into:** Nothing — aggregates results from parallel agents

---

## subagent-driven-development

- **Purpose:** Execute implementation plans in the current session using fresh subagents with two-stage review per task
- **Triggers when:** Plan is ready and user wants same-session execution with quality gates
- **Inputs:** Plan document path
- **Outputs:** Implemented, reviewed, and committed code
- **Tools required:** Read, Agent
- **Chains into:** `git-worktree-workflow` (finish phase), `requesting-code-review`

---

## skill-manager

- **Purpose:** Visibility and management of Claude Code skills across all scopes
- **Triggers when:** User asks what skills they have, wants to install or remove skills, or wants to set up a new project
- **Inputs:** Optional scope flag (global / project / available)
- **Outputs:** Skill inventory; install/remove actions
- **Tools required:** Bash, Read
- **Chains into:** Nothing — terminal skill

---

## writing-skills

- **Purpose:** TDD-based methodology for creating and improving skills
- **Triggers when:** Creating a new skill or editing an existing one
- **Inputs:** Skill concept or existing skill to improve
- **Outputs:** Tested and deployed skill file
- **Tools required:** Read, Write, Agent
- **Chains into:** Nothing — terminal skill

---

## brainstorming

- **Purpose:** Turn ideas into validated specs through collaborative design dialogue
- **Triggers when:** User has an idea or requirement that hasn't been designed yet
- **Inputs:** Raw idea or feature request
- **Outputs:** Approved spec document saved to docs/superpowers/specs/
- **Tools required:** Read, Write, Glob, Agent
- **Chains into:** writing-plans

---

## writing-plans

- **Purpose:** Create detailed implementation plans from approved specs
- **Triggers when:** Spec is approved and ready for implementation
- **Inputs:** Spec document path
- **Outputs:** Implementation plan saved to docs/superpowers/plans/
- **Tools required:** Read, Write
- **Chains into:** subagent-driven-development or executing-plans

---

## executing-plans

- **Purpose:** Execute implementation plans in a fresh parallel session with review checkpoints
- **Triggers when:** Plan is ready and user wants parallel session handoff
- **Inputs:** Plan document path
- **Outputs:** Implemented and reviewed code, committed to branch
- **Tools required:** Read, Agent
- **Chains into:** git-worktree-workflow (finish phase)

---

## tdd

- **Purpose:** Test-Driven Development — write tests before implementation code
- **Triggers when:** About to write any implementation code for a feature or bugfix
- **Inputs:** Feature description or bug report
- **Outputs:** Tests written and passing; implementation guided by tests
- **Tools required:** Bash, Read, Write
- **Chains into:** verification-before-completion, requesting-code-review

---

## systematic-debugging

- **Purpose:** Structured root-cause analysis for bugs and test failures
- **Triggers when:** Encountering a bug, test failure, or unexpected behaviour
- **Inputs:** Bug description, failing test output, or unexpected behaviour description
- **Outputs:** Root cause identified; minimal fix applied; tests passing
- **Tools required:** Bash, Read, Grep
- **Chains into:** tdd (if fix requires new tests), verification-before-completion

---

## verification-before-completion

- **Purpose:** Final verification gate before claiming work is done
- **Triggers when:** About to claim work is complete, fixed, or ready for review
- **Inputs:** List of requirements or acceptance criteria
- **Outputs:** Verification report; confirmed pass or list of remaining issues
- **Tools required:** Bash, Read
- **Chains into:** requesting-code-review

---

## requesting-code-review

- **Purpose:** Structured code review of completed implementation
- **Triggers when:** Implementation complete and verified; ready for review before merging
- **Inputs:** Git diff or file list; spec or requirements
- **Outputs:** Code review report with prioritised findings
- **Tools required:** Bash, Read, Agent
- **Chains into:** git-worktree-workflow (finish phase)

---

## receiving-code-review

- **Purpose:** Structured handling of incoming code review feedback
- **Triggers when:** Receiving review comments and about to act on them
- **Inputs:** Review comments
- **Outputs:** Implemented fixes; re-review confirmation
- **Tools required:** Read, Write, Bash
- **Chains into:** verification-before-completion, requesting-code-review

---

## simplify

- **Purpose:** Post-implementation cleanup — reduce complexity, improve clarity without changing behaviour
- **Triggers when:** Implementation is working and tests pass; time to refine
- **Inputs:** Recently written or modified files
- **Outputs:** Cleaner, simpler code with the same behaviour
- **Tools required:** Read, Write, Bash
- **Chains into:** requesting-code-review

---

## git-expert

- **Purpose:** Version control context manager — worktrees, branches, merge, cleanup
- **Triggers when:** Task needs isolation, branching, worktree setup, git ops, or cleanup
- **Inputs:** Task description, target directory, base branch (optional)
- **Outputs:** Worktree path, branch name, assigned port, active worktree list
- **Tools required:** Bash, Read, Glob
- **Chains into:** git-worktree-workflow, any skill that needs a working directory

---

## git-worktree-workflow

- **Purpose:** Full worktree lifecycle — create isolated workspace and complete/merge work
- **Triggers when:** Starting feature work needing isolation (setup) OR implementation is complete (finish)
- **Inputs:** Branch name and feature description (setup) OR completed branch (finish)
- **Outputs:** Ready worktree with clean baseline (setup); merged/PR'd branch with cleaned-up worktree (finish)
- **Tools required:** Bash
- **Chains into:** Implementation skills (after setup); nothing after finish

---

## github-expert

- **Purpose:** GitHub and gh CLI specialist — repos, PRs, issues, Actions, browsing external repos
- **Triggers when:** Any GitHub task — viewing PRs, checking CI, browsing an external repo, creating issues, managing releases
- **Inputs:** Repo reference (owner/repo or current project), task description
- **Outputs:** Repo info, PR/issue lists, run logs, file contents from any repo via gh api
- **Tools required:** Bash
- **Chains into:** research-agent (broader investigation), api-architect (inspecting external API patterns)

---

## api-architect

- **Purpose:** API contract design and review
- **Triggers when:** Designing new endpoints or reviewing existing API surface
- **Inputs:** Feature description / user story (design mode) OR codebase path (review mode)
- **Outputs:** API contract (markdown or OpenAPI YAML) OR review report with prioritised findings
- **Tools required:** LSP, Bash, Read, Grep, Glob
- **Chains into:** git-expert (for worktree before implementation), docs-agent (for library reference during design)

---

## docs-agent

- **Purpose:** Technical reference lookup — exact APIs, config options, working examples
- **Triggers when:** Need current docs for a library, framework, SDK, API, or CLI tool
- **Inputs:** Library/framework name, version (optional), specific question
- **Outputs:** API signature, working example, source URL, version note
- **Tools required:** WebSearch, WebFetch, mcp__context7
- **Chains into:** api-architect (feeds reference into design), research-agent (supplements analysis)

---

## research-agent

- **Purpose:** General research and critical analysis — consensus, trade-offs, pitfalls
- **Triggers when:** Need to evaluate an approach, understand risks, or find expert consensus before committing
- **Inputs:** Research question or topic
- **Outputs:** Structured report: consensus, nuances, pitfalls, contradictions, recommended direction
- **Tools required:** WebSearch, WebFetch, Read
- **Chains into:** api-architect (informs design decisions), complex-orchestrator (feeds findings into planning)

---

## Chaining Patterns

### Full Feature Flow (with planning)
```
simple-orchestrator → complex-orchestrator
  → brainstorming (idea → spec)
  → writing-plans (spec → plan)
  → git-worktree-workflow (setup worktree)
  → subagent-driven-development (execute plan)
  → git-worktree-workflow (finish + merge)
```

### Quality Gate Flow
```
tdd (write tests first)
  → [implementation]
  → verification-before-completion
  → requesting-code-review
  → git-worktree-workflow (finish)
```

### API Design Only
```
simple-orchestrator → api-architect
  → docs-agent (reference lookup during design)
```

### Quick Research
```
simple-orchestrator → research-agent
```

### Parallel Debug
```
simple-orchestrator → dispatching-parallel-agents
  → systematic-debugging × N (one per independent failure domain)
```

### Parallel Research + Docs
```
simple-orchestrator → complex-orchestrator
  → research-agent ──┐ (parallel)
  → docs-agent    ──┘
  → api-architect (synthesises both)
```
