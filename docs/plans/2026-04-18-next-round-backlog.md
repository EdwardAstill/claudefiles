# Next Round Backlog — 2026-04-18

Fresh observations after the first-round backlog execution (commits
`e28f736` → `c020595`). Not a rehash — these are items that either
emerged from running the telemetry we just built, or are the natural
next step for the 4 deferred design plans in this directory.

Each item carries a status column. Items are grouped into tiers. The
bottom of the doc lists the top-5 for a focused session.

---

## Tier 1 — Cash in a deferred design plan

| # | Item | Spec | Effort | Status |
|---|---|---|---|---|
| N1 | Implement `includes/` fragments | `2026-04-18-includes-fragments.md` | 1 day | **done** — loader + 6 fragments + 4 experts migrated (python, rust, typescript, typst); ui/tui skipped (design skills, no shared fragment) |
| N2 | Implement behavioral modes | `2026-04-18-behavioral-modes.md` | 2–3 days | **done (MVP)** — `modes/` primitive + `af mode` CLI + `hooks/modes.py` + token-efficient + caveman ported. 4 other modes (deep-research, verify-first, rubber-duck, planner) deferred. |
| N3 | Implement typed hook payloads | `2026-04-18-typed-hook-payloads.md` | 1 day | deferred |
| N4 | Implement plan YAML schema | `2026-04-18-plan-yaml-schema.md` | 2 days | deferred |

## Tier 2 — Act on telemetry exposed by round 1

| # | Item | Signal | Effort | Status |
|---|---|---|---|---|
| N5 | Fix 34 manifest drift issues flagged by `af audit` | `af audit` | half session | **in progress** |
| N6 | Prune or archive the 32 never-loaded skills | `af skill-usage` | half session | **in progress** |
| N7 | `af audit --fix` auto-repair mode | repeated manual repair cost | 1 hour | **in progress** |

## Tier 3 — Close half-built loops from round 1

| # | Item | Gap | Effort | Status |
|---|---|---|---|---|
| N8 | Wire `executor` to consume `next:` metadata | metadata exists, unread | 30 min | **in progress** |
| N9 | Real `af learn promote` pipeline (actually move + register, not just echo) | promote is dry-run only | 1 hour | **in progress** |
| N10 | Run `skill-tester` on top-3 busiest skills | never run on real skills | 1–2h wall-clock | deferred (costs API tokens + time) |

## Tier 4 — New capabilities

| # | Item | Why | Effort | Status |
|---|---|---|---|---|
| N11 | `af skill find <query>` keyword search | 73 skills, no search | 30 min | **in progress** |
| N12 | `af archetype run <id>` to scaffold from archetype | match exists, exec missing | 1 hour | deferred |
| N13 | `.claude-plugin/` manifest for marketplace install | distribution gap per anthropics/skills | 2 hours | **in progress** |
| N14 | `af metrics` aggregate dashboard | scattered signals, no summary | 1 hour | **in progress** |
| N15 | Rewrite all 73 skill descriptions as trigger specs | highest-ROI routing improvement | 1 day (parallel batched) | **in progress — top 10 this session** |

## Tier 5 — Polish

| # | Item | Effort | Status |
|---|---|---|---|
| N16 | Sync `hooks/install-gemini-hooks.sh` with `install-hooks.sh` | 15 min | **done** |
| N17 | Filter non-agentfiles skills from `af skill-usage` output | 15 min | **done** |
| N18 | More entries in `research/projects/education-and-showcases/` | half session | deferred |
| N19 | Copy remaining Claude Code `feature-dev:*` subagents locally | 1 hour | deferred |
| N20 | Formalise hook tests into `hooks/tests/` | 1 hour | **done** |

## Tier 6 — Rough edges noticed during execution

Added 2026-04-18 late-session pass as they surfaced.

| # | Item | Signal | Effort | Status |
|---|---|---|---|---|
| N21 | `af learn propose` slug still includes raw path fragments (e.g. `skill-home-eastill-projects-agentfiles-skills-ag`) — smarter keyword selection needed. Filter or collapse `/`-heavy tokens, prefer short meaningful nouns. | user observation after N15 ran | 30 min | open |
| N22 | Node / bun / Python deps in `~/.claude/skills/hooks/*` aren't validated at install time — a hook that imports a missing package fails silently on first trigger. Add an `af check hooks` (or fold into `af audit`) that dry-runs each hook script against `/dev/null` input and reports import errors. | user observation after multiple hook churn | 1 hour | open |
| N23 | Design plans in `docs/plans/2026-04-18-*.md` rot if they sit. Of 5 originally deferred, 2 now done (includes/, behavioral-modes MVP). 3 remain: typed-hook-payloads (N3), plan-yaml-schema (N4), and the next-round-backlog itself when all rows land. Schedule one per focused session rather than letting them sit. | this doc | per-plan effort already listed | see N3, N4, backlog-archive |
| N24 | `af learn promote --apply` was tested on a scratch draft but not yet on a real candidate that survives review. First production promote is the remaining verification gap. | verification gap #4 | 30 min | open |

---

## Execution order (this session)

1. **N5 + N7** — drift-fix + `--fix` mode (auto-repairs most of what N5 needs)
2. **N8** — executor reads `next:`
3. **N9** — learn promote
4. **N11** — skill find
5. **N14** — metrics
6. **N16 + N17** — polish
7. **N20** — hook tests
8. **N6** — prune pass (depends on having N17 running to filter noise)
9. **N1** — includes/ fragments (parallel agent; full implementation)
10. **N13** — `.claude-plugin/` manifest (parallel agent)
11. **N15** — rewrite top-10 description frontmatters (parallel agent, batched)

Deferred with reason:
- **N2, N3, N4** — multi-day design implementations; one at a time when user picks
- **N10** — skill-tester runs cost real API tokens and 1–2h wall-clock; run on demand
- **N12** — wait until N4 (plan YAML) lands
- **N18, N19** — minor polish; batch with a future drift pass

---

## Deletion policy

This plan self-deletes when every non-deferred row has `Status: done` and
the 4 remaining deferred rows are either moved to `archive/` or
converted into their own plan files. Don't keep a half-checked TODO
list in `docs/plans/` — archive when done.
