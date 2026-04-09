# Skills Reference

Skills live in `dev-suite/` organized into three categories. Run `cf-agents --tree` to see the live hierarchy.

## management/ — orchestration and tooling

| Skill | Purpose |
|-------|---------|
| `simple-orchestrator` | Always-on triage — routes simple tasks directly, escalates complex ones |
| `complex-orchestrator` | Full planner — reads the registry, coordinates multi-skill workflows |
| `agent-manager` | Skill visibility and management — what's installed globally vs per-project |

## coding/ — writing, reviewing, and shipping code

| Skill | Purpose |
|-------|---------|
| `git-expert` | Version control manager — worktrees, branches, merge, cleanup |
| `github-expert` | GitHub and gh CLI specialist — PRs, issues, Actions, browsing external repos |
| `api-architect` | API design (from feature → contract) and review (existing code) |
| `coding-quality` | Dispatcher for TDD, debugging, verification, code review (coming soon) |

## research/ — information before action

| Skill | Purpose |
|-------|---------|
| `docs-agent` | Technical reference lookup — exact APIs, examples, versioned docs |
| `research-agent` | General research and critical analysis — consensus, trade-offs, pitfalls |

## Orchestration

`simple-orchestrator` activates on every task and either routes directly to a specialist or escalates to `complex-orchestrator` for full multi-skill coordination.

## Adding a skill

1. Decide which category: `management/`, `coding/`, or `research/`
2. Create `dev-suite/<category>/[sub-category/]<skill-name>/SKILL.md` with `name` and `description` frontmatter
3. Add a `scripts/` folder if the skill needs helper scripts
4. Add an entry to `manifest.toml` under `[skills.<skill-name>]`
5. Add an entry to `dev-suite/registry.md` with inputs, outputs, and chain targets
6. Re-run `./install.sh --global` (symlink picks up changes on next session)
