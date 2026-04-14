# Management Region

Skills for orchestration, coordination, and skill system tooling.

---

### using-agentfiles
- **Purpose:** Session-start enforcement skill — establishes skill-checking rules, 2-path routing system, and how to invoke skills
- **Use when:** Start of every conversation (automatic session-start trigger)
- **Produces:** Active skill-checking discipline for the session
- **Chains into:** executor (first action on every new task)

### executor
- **Purpose:** Default agent for all new tasks — orients, makes routing decision inline, handles end-to-end, absorbs specialist skills inline
- **Use when:** Every new task (not follow-ups); executor self-escalates to manager if parallel multi-agent coordination is needed
- **Produces:** Completed task output with verification evidence
- **Chains into:** (terminal; escalates to manager if parallel coordination discovered)

### manager
- **Purpose:** Coordinator for genuinely multi-agent work — parallel domains, or scale that overwhelms a single context
- **Use when:** Executor escalates here — parallel agents needed, or 20+ independent subtasks across multiple domains
- **Produces:** Executed multi-agent workflow
- **Chains into:** Any specialist skill (via subagent dispatch)

### design-advisor
- **Purpose:** Determines whether a task needs brainstorming or a written spec before implementation
- **Use when:** Manager's planning phase — load when requirements feel underspecified or implementation is complex enough to need a formal plan
- **Produces:** Direct recommendation: brainstorm first / write-plans first / proceed directly
- **Chains into:** (planning phase only — no execution chaining)

### git-advisor
- **Purpose:** Recommends git strategy for the work: isolation level, branching, PR approach, commit structure
- **Use when:** Manager's planning phase — load when the right git approach isn't obvious (multiple agents, risky changes, unclear isolation needs)
- **Produces:** Concrete git strategy: named approach + where in the plan to apply it
- **Chains into:** (planning phase only — no execution chaining)

### coordination-advisor
- **Purpose:** Determines optimal agent coordination structure: parallel vs sequential, team composition, dependency graph
- **Use when:** Manager's planning phase — load when it's unclear which tasks can run in parallel or how to split work across agents
- **Produces:** Dependency graph + concrete coordination plan: which agents run when, what each produces
- **Chains into:** (planning phase only — no execution chaining)

### subagent-driven-development
- **Purpose:** Execute an implementation plan task-by-task with fresh subagent + two-stage review per task
- **Use when:** Have an implementation plan; want sequential execution with review gates in this session
- **Produces:** Committed, reviewed implementation
- **Chains into:** git-worktree-workflow (finish), code-review

### agentfiles-manager
- **Purpose:** View, install, and remove skills across global and project scopes
- **Use when:** User wants to see what skills are installed, install new ones, or remove old ones
- **Produces:** Installed/removed skills; listing of current skill state
- **Chains into:** (terminal)

### writing-skills
- **Purpose:** Create or edit SKILL.md files following the agentfiles format
- **Use when:** User wants to author a new skill or edit an existing one
- **Produces:** New or updated SKILL.md with valid frontmatter and structured body
- **Chains into:** agentfiles-manager (install after writing)

### skills
- **Purpose:** Display the full agentfiles skill catalog grouped by category
- **Use when:** User wants to see all available skills and their invocation names
- **Produces:** Formatted catalog output
- **Chains into:** (terminal)
