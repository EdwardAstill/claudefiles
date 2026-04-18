# docs/

Current-state documentation for agentfiles. Not long-term memory —
`research/` is the long-term memory tree.

## What lives here

| Path | Purpose |
|---|---|
| `reference/` | Canonical design specs: how the system works today (orchestration, skills, install, hooks, workflows, task-archetypes). Read at runtime by skills. |
| `plans/` | Implementation plans — design docs waiting to be executed. Dated `YYYY-MM-DD-<topic>.md`. Move to `plans/archive/` once implemented. |
| `plans/archive/` | Executed plans, kept for historical reference. |
| `specs/` | Feature-level specifications produced by `brainstorming` before planning begins. |
| `skills-drafts/` | Candidate SKILL.md drafts emitted by `af learn`. Require human review before promotion into `agentfiles/`. |
| `agent-performance/` | Performance benchmarks for subagents. |
| `testing/` | Rubric reports from `skill-tester` runs. |
| `examples/` | Worked examples, sample inputs. |
| `tools/` | Documentation for external CLI/MCP tools the system depends on. |
| `skill-tree.md` | Generated skill hierarchy overview. |

## What does NOT live here

- **Long-term knowledge / research syntheses** → `research/knowledge/`
- **Session retrospectives** → `research/lessons/`
- **External repo summaries** → `research/projects/`
- **Local copies of third-party platform docs** → `research/documentation/`
- **Academic papers** → `research/papers/`

`docs/` is for *our own authored documentation*. `research/` is for *everything
we've learned from elsewhere plus our own distilled conclusions*.
