# Dev Suite Registry

Read by `complex-orchestrator` to understand skill contracts and plan multi-skill workflows.
Keep this in sync when adding or changing skills.

---

## Taxonomy

Skills are organized into three top-level categories. Each category has a dispatcher skill
that routes to the right leaf skill. Run `cf-agents --tree` to see the live hierarchy.

```
dev-suite/
├── management/           ← orchestration, planning, agent tooling
│   ├── orchestration/
│   │   ├── simple-orchestrator
│   │   └── complex-orchestrator
│   └── agent-manager
├── coding/               ← code writing, review, version control, API design
│   ├── quality/          (tdd, debugging, verification, review — coming soon)
│   ├── version-control/
│   │   ├── git-expert
│   │   └── github-expert
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

## git-expert

- **Purpose:** Version control context manager — worktrees, branches, merge, cleanup
- **Triggers when:** Task needs isolation, branching, worktree setup, git ops, or cleanup
- **Inputs:** Task description, target directory, base branch (optional)
- **Outputs:** Worktree path, branch name, assigned port, active worktree list
- **Tools required:** Bash, Read, Glob
- **Chains into:** Any skill that needs a working directory (always run git-expert first when worktrees are needed)

---

## api-architect

- **Purpose:** API contract design and review
- **Triggers when:** Designing new endpoints or reviewing existing API surface
- **Inputs:** Feature description / user story (design mode) OR codebase path (review mode)
- **Outputs:** API contract (markdown or OpenAPI YAML) OR review report with prioritised findings
- **Tools required:** LSP, Bash, Read, Grep, Glob
- **Chains into:** `git-expert` (for worktree before implementation), `docs-agent` (for library reference during design)

---

## docs-agent

- **Purpose:** Technical reference lookup — exact APIs, config options, working examples
- **Triggers when:** Need current docs for a library, framework, SDK, API, or CLI tool
- **Inputs:** Library/framework name, version (optional), specific question
- **Outputs:** API signature, working example, source URL, version note
- **Tools required:** WebSearch, WebFetch, mcp__context7
- **Chains into:** `api-architect` (feeds reference into design), `research-agent` (supplements analysis with concrete docs)

---

## research-agent

- **Purpose:** General research and critical analysis — consensus, trade-offs, pitfalls
- **Triggers when:** Need to evaluate an approach, understand risks, or find expert consensus before committing
- **Inputs:** Research question or topic
- **Outputs:** Structured report: consensus, nuances, pitfalls, contradictions, recommended direction, further investigation pointers
- **Tools required:** WebSearch, WebFetch, Read
- **Chains into:** `api-architect` (informs design decisions), `complex-orchestrator` (feeds findings into planning)

---

## github-expert

- **Purpose:** GitHub and gh CLI specialist — repos, PRs, issues, Actions, browsing external repos
- **Triggers when:** Any GitHub task — viewing PRs, checking CI, browsing an external repo, creating issues, managing releases
- **Inputs:** Repo reference (owner/repo or current project), task description
- **Outputs:** Repo info, PR/issue lists, run logs, file contents from any repo via gh api
- **Tools required:** Bash
- **Chains into:** `research-agent` (broader investigation), `api-architect` (inspecting external API patterns), `cf-note` (recording findings)

---

## agent-manager

- **Purpose:** Visibility and management of Claude Code skills across all scopes
- **Triggers when:** User asks what skills/agents they have, wants to install or remove skills per scope, or wants to understand their Claude Code setup
- **Inputs:** Optional scope flag (global / project / available)
- **Outputs:** Full skill inventory across plugins, global, and project scopes; install/remove actions
- **Tools required:** Bash, Read
- **Chains into:** Nothing — terminal skill, acts directly via install.sh and cf-agents

---

## complex-orchestrator

- **Purpose:** Full multi-skill planning and coordination
- **Triggers when:** simple-orchestrator escalates a high-complexity task
- **Inputs:** User goal, complexity axes that scored HIGH, known context summary
- **Outputs:** Executed multi-skill plan with collected results
- **Tools required:** Read (reads this registry)
- **Chains into:** All skills (coordinates them)

---

## Chaining Patterns

### Feature Development (full flow)
```
simple-orchestrator → complex-orchestrator
  → research-agent (evaluate approach)
  → api-architect (design contract)
  → git-expert (create worktree)
  → [implementation in worktree]
  → git-expert (merge + cleanup)
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

### Parallel Research + Docs
```
simple-orchestrator → complex-orchestrator
  → research-agent ──┐ (parallel)
  → docs-agent    ──┘
  → api-architect (synthesises both)
```
