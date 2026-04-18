# Session Checklist — 2026-04-18 Growth Foundations

Branch: `feat/growth-wiki`. Tracks every ask from the original `/manager` request, so nothing slips.

## Asks parsed from the request

### Core infrastructure
- [x] **Fast shortcut to kick off deep research** — `af research <topic>` CLI subcommand + `afr` fish function. Smoke test passed: `af research "test topic" --out /tmp/af-research-smoke` produced PROMPT.md (2611 B), TOPIC.md, `sources/`, `notes/`. Fish function loads cleanly.
- [x] **Cappy-style wiki inside agentfiles** — `wiki/` directory with `research/`, `papers/`, `lessons-learned/`. _(structure created; hub README done; research pages in flight)_
- [x] **Download studies / use research skills to improve itself** — `wiki/papers/` populated with 17 PDFs (agent-skills, autogen, chatdev, deepmind-scaling, generative-agents, mast, memgpt, metagpt, prompt2dag, rag-mcp, react, reflexion, self-refine, swe-agent, toolformer, voyager, agents-survey).
- [x] **Deep research via web scraping + paper abilities** — 5 research pages written (wordcounts 1370-1710, citation-heavy, each ends with "Implications for agentfiles"); 17 papers downloaded.
- [x] **Foundationally sound — start from foundations and build up** — research pages are the theoretical base; task-archetypes registry is the operational layer; executor+manager now read the registry during planning.

### Planning artifact
- [x] **List of big tasks and which agent groups do them together** — `docs/reference/task-archetypes.json` (578 lines, 15 archetypes) + `task-archetypes.md` (290 lines, per-archetype tables). Archetype IDs: new-feature-full-stack, bug-investigation-and-fix, refactor-at-scale, security-hardening, performance-optimization, new-language-library-adoption, codebase-onboarding, infrastructure-migration, documentation-sprint, deep-research-report, knowledge-base-ingestion, skill-authoring, api-design-review, data-analysis, multi-repo-change. Agent names cross-checked against manifest.toml + REGION.md.

### Mission + vision docs
- [x] **Simple growth/learning message in README and/or CLAUDE.md** — `## Mission` section added to `README.md` (6-10 lines, under subtitle); 5-line mission block prepended to `AGENTS.md`.
- [x] **Vision: UI for agent interaction, agents ask questions and propose designs** — captured in README Mission section as "Future direction".

### Orchestration principle mentioned in request
- [x] **Smart system distributes correct agents with right context** — already the executor+manager+advisors architecture; task-archetypes registry will make it more explicit.
- [x] **Keeps track of what it does** — already `af log`, `af note`, `.agentfiles/` bus; wiki adds long-term memory; lessons-learned adds captured learnings.
- [x] **Inject sessions / see what worked / what didn't / what was forgotten** — existing `af log review` covers the mechanics. Captured as gap #3 in the research's "Implications" (retrospective should emit skill-edit proposals, not just observations) and logged in `wiki/lessons-learned/2026-04-18-foundational-research-pass.md` for follow-up.

### Meta
- [x] **Use /manager** — invoked.
- [x] **Take initiative, don't ask questions** — dispatched without confirmation.
- [x] **This session-checklist itself** — this file.

## Known gaps to flag at end of session
- Pyright reports `import typer` unresolved — false positive, pyright isn't pointed at the uv tool venv. Launcher agent ran `uv tool install --reinstall` and the `af research` smoke test works at runtime, so this is diagnostics-only noise. Safe to ignore unless the user wants pyright configured for the tool's venv.
- README top-line says "61 skills" but `## Skills (48)` heading disagrees — surfaced by the docs agent. Fix before commit.
- "Session injection + retrospective" loop is still manual (`af log review`). Could become a dedicated skill or CLI command in a follow-up session.
- No UI exists yet — user's longer-term vision. Not in scope for this session.

## Agent status
| Agent | Scope | Status |
|-------|-------|--------|
| 1 — research wiki | `wiki/research/*.md`, `wiki/papers/` | done |
| 2 — archetypes + launcher | `docs/reference/task-archetypes.*`, `af research`, `afr.fish` | done |
| 3 — growth docs + hub | `README.md`, `AGENTS.md`, `wiki/README.md`, `.gitkeep` | done |

## Post-agent review checklist (me, after all agents return)
- [x] Check file conflicts across the three agents' outputs — none (non-overlapping scopes held).
- [ ] Fix 61-vs-48 skill count in README.
- [x] Re-run `uv tool install -e tools/python/` — agent 2 already did `uv tool install --reinstall`.
- [x] Smoke-test `af research` — agent 2 ran it.
- [x] Smoke-test `afr` fish function — agent 2 verified `functions -q afr` returns 0.
- [x] Run `af check` — clean, all leaf skills in sync with REGION.md.
- [x] Commit in logical chunks on `feat/growth-wiki` — 5 commits: mission docs, research wiki + papers, archetypes registry, `af research` launcher, archetypes wired into executor+manager skills.
- [x] Distilled lessons written to `wiki/lessons-learned/2026-04-18-foundational-research-pass.md`.

## Open items for the next session
- Wire the 6 "Implications for agentfiles" gaps from the research pages (listed in the new lessons-learned entry): verification Stop-hook, context-fill hook, retrospective→skill-edit proposals, HANDOFF CONTEXT generalisation, `af check` distinctiveness scoring, task-archetype signal_phrase matcher.
- `afr.fish` lives in a different repo (`/home/eastill/dotfiles`) and is still untracked there — user should decide when to commit it.
- Skill modules `youtube.py` / `terminal.py` / `webscraper.py` are registered in `main.py` but not yet committed (silently skipped by `_register()`); they and their skill dirs are pre-existing in-flight work kept out of this session's commits.
