# Next Steps

Handoff doc for picking up agentfiles after the 2026-04-18 session.

Read this before touching anything. The repo is in its best shape of the
session — no open regressions, no half-shipped features, everything
committed and pushed. What follows is ranked optional work.

---

## 1. State at session end

**Commits:** `e28f736` → `6e33bd2` (14 commits, all on `main`, all pushed).

**Verification:**

```
pytest: 201 passed, 1 skipped
af audit: 9/9 checks passed, 0 issues
af check plans: 1 pair clean, no drift
safety-gate tests: 18/18 passed
plugin validator: .claude-plugin/{plugin,marketplace}.json both valid
```

**Scale:**

- **73 skills** registered across 4 top-level categories
- **10 subagents** in `agentfiles/agents/` (3 custom: skill-tester, audit, security-review; 7 local copies of Claude Code built-ins)
- **2 behavioral modes** (token-efficient, caveman)
- **5 knowledge pages** (K-001..K-005) in `research/knowledge/`
- **6 includes/ fragments** across python, typescript, rust, typst
- **9 audit checks** (skill/agent/cli registry + hook script health)

**CLI surface** (24 top-level subcommands, plus install/research):

```
af ak {list,show,grep}
af archetype {match,show,list}
af audit [--fix]
af caveman {on,off,status}       # backwards-compat alias → af mode caveman
af check {distinct,plans}
af context / af status / af versions / af routes / af tree
af include {list,show,expand,check}
af learn {propose,list,promote}
af log {session,analyze,anomalies,review}
af metrics
af mode {list,on,off,status}
af note / af read / af init
af plan-exec {validate,list,next,mark,reset,status}
af plan-scaffold
af skill-find
af skill-usage {summary,rank,sessions}
af test-skill
af terminal / af webscraper / af youtube {transcript,audio,summary,channel,playlists,search}
af hub / af repo / af setup / af tools / af secrets / af preview / af screenshot / af worktree
```

---

## 2. What shipped this session

One-liner per commit, bottom-up (newest last):

| Hash | Message |
|---|---|
| `e28f736` | Removed 46 broken self-referential symlinks inside skill dirs |
| `da71e8a` | Added local subagent library (3 custom + 7 local copies of built-ins) |
| `c0d5715` | Landed youtube/terminal-read/web-scraper/reasoning suite |
| `625ca23` | Deleted make-quiz, folded quiz authoring into readrun |
| `114e68f` | Renamed `wiki/` → `research/` with distilled `knowledge/` subdir + `af ak` CLI |
| `b7650f8` | `af youtube search` + artist → WAV workflow |
| `2518a75` | Research pass: claude-mem + anthropic-best-practices + refreshed hermes/archon |
| `1762736` | Implemented 5 research gaps (Plan Mode, batch loop, SessionStart enrichment, AskUserQuestion, K-NNN ids) |
| `c020595` | 18-item backlog: `af audit`, `af skill-usage`, `af learn`, `af metrics`, `af skill-find`, `af include`, trigger-spec descriptions, `.claude-plugin` manifest, hooks/README, smoke tests |
| `1a89644` | Fixed 3 verification gaps (slug, promote name-drift, plugin schema) |
| `cbf5be6` | Safety-gate: whitelist → blacklist (catastrophic-only) |
| `82bb30c` | 3 parallel agents: includes/ migration, behavioral modes MVP, dsa-expert skill-tester run |
| `043c187` | Tier-6 rough edges: slug generator, hook-dep validation, promote pipeline test |
| `0b311ac` | N3 typed hook payloads (4 hooks + shared hook_types module) |
| `8f16e15` | N4 phase 1 (plan YAML core loader + validator + toposort) |
| `4143616` | N4 phase 2 (CLI + writing-plans + skill wiring + drift watchdog) |
| `6e33bd2` | N4 phase 3 (first real YAML sidecar dogfooded end-to-end) |

---

## 3. Open items — ranked by leverage

### Tier A — Highest leverage (do these first)

| # | Item | Effort | Why |
|---|---|---|---|
| **A1** | **Prune 32 never-loaded skills** | 4 hours | `af skill-usage summary --days 90` shows 32/73 skills have never been loaded. Run through each, archive/merge/reword. Biggest concrete catalog improvement remaining. Judgment-heavy — can't be done by an agent without review. |
| **A2** | **Rewrite remaining ~63 skill descriptions as trigger specs** | Half day (batchable in parallel agents) | Only top-10 were done this session. The routing-quality lift scales linearly. Per-skill: add 5–10 trigger phrases + 2–3 negative scope clauses. anthropics/skills-style. |
| **A3** | **Ship `skill-tester` on `codebase-explainer` and `research-agent`** | 1–2 hours wall-clock | Only dsa-expert has a real benchmark today. These two are the next-best candidates — concrete rubric-gradable outputs. Result goes in `docs/testing/`. |

### Tier B — Concrete follow-ups to items already shipped

| # | Item | Effort | Why |
|---|---|---|---|
| **B1** | **Ship 4 remaining behavioral modes** (deep-research, verify-first, rubber-duck, planner) | 1 hour each | MODE.md primitive already supports them. Each one is just a file + reminder text + category classification. See `docs/plans/2026-04-18-behavioral-modes.md`. |
| **B2** | **Retire old caveman SKILL.md + its manifest entry** | 30 min | The new `agentfiles/modes/caveman/MODE.md` is the real caveman now. Old SKILL.md still exists because several callers (marketplace blurb, `hooks/install-*.sh`, `docs/skill-tree.md`, `tools/python/tests/test_cli_smoke.py`) reference it. One-pass migration. |
| **B3** | **Delete `hooks/caveman-mode.py` shim** | 5 min | Was kept as one-release grace for cached plugin configs. Safe to delete now. |
| **B4** | **Fix `af learn` dogfooding issues** | 1 hour | Three related follow-ups flagged during N24 testing: (a) exclude `$CLAUDE_SESSION_ID` from session file scan so mid-session `af learn propose` doesn't hit a moving target; (b) clean path-noise tokens out of the `description` field (not just the slug); (c) add `2 > /dev/null` redirect tokens to `_STOP_TOKENS` to avoid slugs like `2-dev-null-…`. |
| **B5** | **Wire `af check plans` into pre-commit / CI** | 30 min | Drift watchdog exists but nothing invokes it automatically. Add to either `.git/hooks/pre-commit` or a new section of `af audit` check 10. |

### Tier C — Infrastructure polish

| # | Item | Effort | Why |
|---|---|---|---|
| **C1** | **Archive shipped design plans** | 15 min | `docs/plans/2026-04-18-{includes-fragments,behavioral-modes,typed-hook-payloads,plan-yaml-schema}.md` all shipped. Move to `docs/plans/archive/` to signal "done, don't re-plan." Keep the markdown header `**Status:** shipped YYYY-MM-DD`. |
| **C2** | **Copy remaining Claude Code built-in subagents locally** | 1 hour | Have 7 of 10. Missing: `feature-dev:feature-dev`, `feature-dev:code-reviewer`(?), `statusline-setup`. Check the session's opening system reminder for the canonical list. |
| **C3** | **Populate `research/projects/education-and-showcases/`** | 1 hour | Only 3 entries today. Candidates: anthropic/courses, specific agent demos, tutorial repos the session browsed. |
| **C4** | **Add monthly `af log review` cron or scheduled trigger** | 30 min | The self-improvement loop exists (`af log review` + retrospective skill + promotion rule). Nothing runs the crank. Options: shell cron, systemd timer, `schedule` skill. |
| **C5** | **StateFile.mark loop-body id handling** | 30 min | Phase 2A noted: `mark` accepts ids for nodes inside a `LoopNode.body`. Spec is silent on whether that's intentional. Decide: allow (current), or scope loop bodies to their parent loop's state. |

### Tier D — Design candidates (these could become plans)

None of these have written specs yet. Each could be written up and shipped if the need shows.

| # | Item | Why it might matter |
|---|---|---|
| **D1** | **Per-project modes** — `af mode on --project` writes to `.claude/modes/` in the repo. | Mentioned in `docs/plans/2026-04-18-behavioral-modes.md` §9 as deferred. Useful if you want a mode active only in one project. |
| **D2** | **Named mode bundles** — `af mode preset research-deepdive` activates a curated set. | Deferred per same plan. Lower priority until people are using modes more. |
| **D3** | **Retire `agentfiles/communication/caveman/SKILL.md`** fully | Already covered in B2 — noting here because the follow-ups chain. |
| **D4** | **Skill-tester workflow automation** — `af test-skill <name>` scaffolds workspace + dispatches subagent + renders report. | Already partially implemented, but the pipeline is manual-click today. |
| **D5** | **Per-skill `model:` frontmatter** (like anthropics/skills does) | Route cheap skills to haiku, expensive orchestration to opus. Would need hook-time routing change. |
| **D6** | **Eval-viewer for `skill-tester`** | anthropics/skills ships an eval-viewer in skill-creator. We have the data in `tests/<skill>/iteration-N/` — an HTML viewer would make reviewing benchmark deltas faster. |

### Tier E — Small fixes / rough edges

| # | Item | Effort |
|---|---|---|
| **E1** | **`af audit` check 9 shell-binary scan is best-effort** — false positives on `command -v`-guarded binaries. Documented, not a bug; consider skipping binaries inside `command -v <bin>` contexts if noise grows. | 30 min |
| **E2** | **python-expert vs typescript-expert similarity 0.42** per `af check distinct`. Benign template pairing; revisit if routing actually confuses them. | 10 min |
| **E3** | **hooks/install-gemini-hooks.sh parity** should be audited periodically. Synced this session; drift will return. | 15 min |
| **E4** | **`skill-logger.py` reads `tool_output`/`output` but canonical schema uses `tool_response`** | 15 min |
| **E5** | **Gitignore `tools/python/tests/fixtures/plan_example.yaml.state.json`** if tests ever leak state | 5 min |

---

## 4. How to pick this back up

First 5 minutes:

```bash
cd ~/projects/agentfiles
af metrics                       # overall health
af audit                         # must be 9/9
af skill-usage summary --days 30 # what's used, what's dead
af ak list                       # what knowledge exists
cat docs/plans/2026-04-18-next-round-backlog.md   # item-level backlog
cat NEXT_STEPS.md                # this file
```

Pick one item from the ranked list. Most tier-A/B items are <1 day and ship cleanly.

---

## 5. Guard rails

Things to NOT do without thinking:

- **Don't bulk-promote every draft under `docs/skills-drafts/`.** The human-in-the-loop gate exists because the heuristic surfaces session replays, not distilled skills. N24's rejection proved this.
- **Don't disable `af audit` checks.** Each one was added in response to real drift. The safety-gate hook similarly catches real blast radius.
- **Don't convert skills to subagents proactively.** Per `docs/reference/skills-vs-subagents.md`, the 3-criteria rule says only convert when verbose-output + self-contained + benefit-from-tool-restriction all hold. We shipped 3 (skill-tester, audit, security-review); that's probably it.
- **Don't add MCP servers / CLI tools preemptively.** The anti-bloat rule in `AGENTS.md` says capability, not surface area. Measure demand before adding.

---

## 6. Unused but installed

Things wired up but not actively used — watch for whether they earn their weight.

- **`af learn`** — works, shipped drafts, none yet promoted. First real promotion will stress-test the flow beyond scratch.
- **`af plan-exec`** — pipeline proven end-to-end, but only one sidecar (retrospective behavioral-modes). Next forward plan should have a YAML from day one.
- **`af skill-find`** — keyword search; low-traffic until the catalog grows.
- **`af check plans`** — drift watchdog; only 1 pair today.
- **`af metrics`** — dashboard; nothing consumes its output yet.

---

## 7. Design plans — all shipped

| Plan | Shipped |
|---|---|
| `docs/plans/2026-04-18-includes-fragments.md` | `8f16e15`... (in the c020595 batch, really) |
| `docs/plans/2026-04-18-behavioral-modes.md` | `82bb30c` (MVP) |
| `docs/plans/2026-04-18-typed-hook-payloads.md` | `0b311ac` |
| `docs/plans/2026-04-18-plan-yaml-schema.md` | `8f16e15` + `4143616` + `6e33bd2` |

Earlier plans already archived: `docs/plans/archive/{2026-04-09-layered-skill-taxonomy,2026-04-14-skill-tester}.md`.

**Tier-C1 follow-up:** move the 4 shipped plans to archive now that they're done. Keeps `docs/plans/` focused on in-flight work.

---

## 8. The one thing to remember

The improvement loop exists and the infrastructure is in place:

```
session → af log review → research/lessons/ → promote pattern → knowledge/K-NNN
                       ↘ anomalies.md → retrospective skill → skill edits
```

Nothing ran the crank automatically this session. The next highest-leverage
operational change is wiring a weekly cron on `af log review`. Until someone
does that, compound learning depends on humans remembering to pull the
handle. See Tier-C4.
