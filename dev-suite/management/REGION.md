# Management Region

Skills for orchestration, coordination, and skill system tooling.

---

### task-analyser
- **Purpose:** Always-on entry point — decomposes tasks, scores complexity, routes to cheapskill/superskill/manager
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
