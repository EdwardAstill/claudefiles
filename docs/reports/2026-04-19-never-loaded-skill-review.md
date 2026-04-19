# Never-Loaded Skill Review — 2026-04-19

Backlog item **1-1** (formerly A1) in `NEXT_STEPS.md` called for pruning 32
never-loaded skills. Actual count at review time: **11 of 73**. The drop from
32 → 11 over the same 90-day window is attributable to the session's work on
A2 (trigger-spec description rewrites), which surfaced leaves to the router.

This document evaluates each of the 11 and records the decision.

## Classification framework

| Type | Meaning | Zero-load default |
|---|---|---|
| Dispatcher | Lives at a category root (`agentfiles/<cat>/SKILL.md`). Routes to leaves. | **Expected.** Dispatchers fire only on ambiguous requests that don't match any leaf trigger. With leaves well-triggered, dispatchers shouldn't load. |
| Leaf | Does real work. | **Investigate.** Possible causes: weak triggers, scope overlap with a louder peer, genuinely niche, or brand-new. |

## The 11 skills

### 1. agentfiles-manager (leaf)

- **Path:** `agentfiles/management/meta/skill-manager/SKILL.md`
- **Description quality:** Trigger-spec (12 phrases, 3 negative scopes) — excellent
- **Overlap:** `audit` validates manifest consistency; `skill-catalog` browses skills; agentfiles-manager owns install/remove/setup. Distinct.
- **Decision:** KEEP
- **Note:** There is a name/path drift — frontmatter says `name: agentfiles-manager`, directory is `skill-manager`, and the system's available-skill listing advertises it as `skill-manager`. The skill-usage logger records `agentfiles-manager`. This inconsistency likely affects routing but is out of scope for this review; tracked as a follow-up.

### 2. coding (dispatcher)

- **Path:** `agentfiles/coding/SKILL.md`
- **Description quality:** Trigger-spec with routing table — excellent
- **Decision:** KEEP
- **Reason:** Dispatcher. Zero-loads expected — leaves (python-expert, tdd, systematic-debugging, code-review, etc.) now trigger directly after A2.

### 3. coding-quality (dispatcher)

- **Path:** `agentfiles/coding/quality/SKILL.md`
- **Description quality:** Trigger-spec with routing table — excellent
- **Decision:** KEEP
- **Reason:** Sub-dispatcher. Routes to tdd / systematic-debugging / verification-before-completion / code-review / simplify / documentation. Zero-loads expected; leaves are heavily used.

### 4. computer-control (leaf)

- **Path:** `agentfiles/research/computer-control/SKILL.md`
- **Description quality:** Trigger-spec (15 phrases, 2 negative scopes)
- **Overlap:** None — sibling `browser-control` is web-only, `terminal-read` is scrollback-only, `computer-control` is Hyprland/Wayland desktop.
- **Decision:** KEEP
- **Reason:** Shipped this session (commit `34eedf3`). Zero-loads expected for a brand-new skill.

### 5. dsa-expert (leaf)

- **Path:** `agentfiles/coding/dsa/SKILL.md`
- **Description quality:** Trigger-spec (9 phrases, 3 negative scopes) — excellent
- **Overlap:** `system-architecture-expert` is service topology; `api-architect` is contracts; `database-expert` is schemas. dsa-expert owns algorithm choice and complexity. Distinct.
- **Benchmark:** `docs/testing/dsa-expert.md` — +4.8/25 rubric delta, recommended.
- **Decision:** KEEP
- **Reason:** Strong description, proven value, legitimate niche. 90-day zero-loads reflect question mix, not skill quality.

### 6. management (dispatcher)

- **Path:** `agentfiles/management/SKILL.md`
- **Description quality:** Trigger-spec with routing table — excellent
- **Decision:** KEEP
- **Reason:** Category dispatcher. `executor` is now the default entry point; users with specific needs route to `manager`, `subagent-driven-development`, etc. directly. Non-load is expected.

### 7. management-meta (dispatcher)

- **Path:** `agentfiles/management/meta/SKILL.md`
- **Description quality:** Trigger-spec with routing table — good
- **Decision:** KEEP
- **Reason:** Sub-dispatcher for skill-system housekeeping. Leaves (agentfiles-manager, writing-skills, audit) catch direct calls after A2.

### 8. planning (dispatcher)

- **Path:** `agentfiles/planning/SKILL.md`
- **Description quality:** Trigger-spec with routing table — excellent
- **Decision:** KEEP
- **Reason:** Routes to brainstorming (no spec yet) or writing-plans (spec ready). Leaves trigger directly now; dispatcher serves genuine "which phase am I in?" ambiguity.

### 9. reasoning (dispatcher)

- **Path:** `agentfiles/reasoning/SKILL.md`
- **Description quality:** Trigger-spec with routing table — excellent
- **Decision:** KEEP
- **Reason:** Routes to game-designer / logic-puzzle-designer / constraint-solver. Specialist niche; zero-loads reflect rarity of the problem class, not dispatcher quality.

### 10. research (dispatcher)

- **Path:** `agentfiles/research/SKILL.md`
- **Description quality:** Brief prose with routing table — good (not full trigger-spec style but adequate)
- **Decision:** KEEP
- **Reason:** Leaves (docs-agent, research-agent, codebase-explainer) have strong triggers post-A2. Dispatcher serves occasional "I need information but don't know which research tool" cases.

### 11. system-architecture-expert (leaf)

- **Path:** `agentfiles/coding/architecture/SKILL.md`
- **Description quality:** Trigger-spec (7+ phrases, 5 negative scopes) — excellent
- **Overlap:** `api-architect` (endpoint contracts, not topology), `database-expert` (schema, not data strategy), `infrastructure-expert` (deployment, not design). Each covers a different stratum. Distinct.
- **Decision:** KEEP
- **Reason:** Well-scoped specialist. Niche questions (monolith vs microservices, boundary placement, scaling strategy) come up sporadically; 90-day zero-loads is legitimate low volume.

## Summary

| Category | Count | Action |
|---|---|---|
| Dispatcher KEEP | 7 | No change. Zero-loads expected post-A2. |
| Leaf KEEP | 4 | No change. One is brand-new; three are niche-but-documented. |
| ARCHIVE / MERGE / DELETE | 0 | None. |

**Verdict:** no catalog changes. The A2 trigger-spec rewrite is the real fix for what backlog item 1-1 originally called out — improved routing drove the never-loaded count from 32 → 11, and the remaining 11 are legitimate (6 dispatchers operating as designed, 4 niche leaves with proven value or brand-new scope, 1 name-drift flagged below).

## Follow-ups surfaced

1. **agentfiles-manager name drift** — directory is `skill-manager`, frontmatter + manifest say `agentfiles-manager`, system skill listing advertises it as `skill-manager`. The skill-usage logger records `agentfiles-manager`. This split naming almost certainly costs routing accuracy and manifest parseability. Rename one way or the other and update all references. Tracked separately; not part of this review.
2. **research dispatcher description** is not full trigger-spec style — brief prose. Low priority (dispatchers don't benefit as much as leaves from heavy triggers, by design), but worth a pass next time the research category is touched.
3. **Monitor the 4 leaves** over the next 30 days. If computer-control, dsa-expert, system-architecture-expert, or agentfiles-manager stay at zero loads despite relevant tasks flowing through the system, the conclusion shifts — likely a trigger-quality issue rather than a volume one.
