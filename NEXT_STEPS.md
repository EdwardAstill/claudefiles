# Next Steps

Handoff + live backlog for agentfiles. Also drives an in-session loop
that ticks every 10 min for 2 hours — see §0.

---

## 0. Cron-bot charter

**Each time the loop fires (every 10 min):**

1. Read this file end-to-end before acting. State lives here.
2. Increment `§1.iteration` counter. Log wall-clock time to `§1.last_tick`.
3. Evaluate stop conditions (below). If any match → run the stop protocol.
4. Pick the item tagged `⭐ NEXT` in §3. If no item is tagged, pick the top unticked item in §3 and tag it.
5. Execute per SOP (below). One item per iteration. Do NOT try to batch.
6. Verify: `af audit` must stay 10/10, `pytest` (from `tools/python/`) must stay 209 passed 1 skipped (or higher if tests were added).
7. Commit + push in a single self-contained commit. Message format: `<type>(<scope>): <what> (<code>)` where `<code>` is the backlog id (e.g. `3-4`, `5-1`).
8. Update this file: move the shipped item from §3 to §2, move `⭐ NEXT` to the new top of §3, add any newly surfaced work as fresh §3 entries (use the next free code in the right tier).
9. End turn.

**Stop conditions (any match → stop):**

- `§1.iteration >= 12` (12 × 10 min = 2 hours)
- Wall clock ≥ `§1.stop_by`
- `§3` contains only items tagged `[speculative]` or `[needs-human]`
- 3 consecutive iterations failed verification

**Stop protocol:**

- Write a one-line entry in `§4` capturing what ran and what's left.
- Commit this file as `chore(cron): stop after N iterations`.
- Push. End turn with a summary to the user.
- Do NOT schedule another /loop.

**SOP per item:**

| Size hint in §3 | Execution |
|---|---|
| `[trivial]` (<10 min, one file) | Inline: Read → Edit → verify → commit |
| `[small]` (one module or a handful of files) | Inline, possibly one parallel Agent for heavy I/O |
| `[medium]` (cross-file, requires discovery) | Single Agent dispatch with focused context |
| `[large]` (split across domains, parallelizable) | Multiple parallel Agents, reconcile after |
| `[needs-human]` | Do not execute. Skip and pick next item. |
| `[speculative]` | Do not execute. Skip and pick next item. |

**Guard rails (do not violate):**

- No destructive git operations without explicit user authorization. `push` and `push --force` are categorically different; only regular `push` is allowed in the loop.
- Never skip hooks (`--no-verify`).
- Never bulk-promote drafts under `docs/skills-drafts/`.
- Never disable `af audit` checks. If a check fails, fix the underlying drift.
- Never write to `~/.claude/` or any path outside this repo. Outside-repo work belongs in §5 for the user to do manually.
- If an item looks like it needs scope discussion, re-tag it `[needs-human]` and skip.

---

## 1. Loop state

- `start_commit`: `23589ba`
- `start_time`: 2026-04-19 (loop-start)
- `stop_by`: start_time + 2 hours
- `iteration`: 3 / 12
- `last_tick`: iter 3 @ 3f577e7 — shipped 3-5 (plan-exec state scoping spec)
- `cron_mode`: self-paced (10m cron replaced; ScheduleWakeup 60s on finish)
- `consecutive_failures`: 0
- `cron_id`: `20ca1e5e` (every 10 min, recurring, 7-day auto-expire)

---

## 2. Shipped

**This active session** (parallel sweep + cron follow-ups).

| Commit | Code | What |
|---|---|---|
| `e89417a` | 2-1, 2-2, 2-3, 3-1, 3-2 | Parallel backlog sweep — 4 behavioral modes, retire old caveman, delete hook shim, archive 4 shipped design plans, copy 4 missing built-in subagents |
| `5a42bf9` | 1-3 | Skill-tester on codebase-explainer (+4.75/25) + research-agent (+3.00/25); both verdict: recommend |
| `baf5567` | 5-5 | Gitignore plan-exec state files recursively |
| `05c7e59` | 1-2 | 60 skill descriptions rewritten as trigger specs (coding 34 / mgmt 11 / research 6 / reasoning+coaches+planning 9) |
| `9bce750` | 2-4 | 3 `af learn` dogfooding defects fixed (active-session skip, title path-noise, redirect STOP_TOKENS) |
| `7b05ae0` | 2-5 | `af audit` CHECK 10 — plan-pair drift detection |
| `033a917` | — | Rename backlog codes A1..E5 → 1-1..5-5 |
| `34eedf3` | — | New `computer-control` skill (Hyprland / dotool / hyprctl / grim / slurp / wl-copy) |
| `dcca1f1` | 1-1 | Never-loaded skill review — verdict KEEP all 11 (6 dispatchers + 4 niche leaves + 1 brand-new). The A2 rewrite already did the real pruning work (never-loaded count fell 32 → 11). |
| `23589ba` | — | Resolve `agentfiles-manager` name drift (dir rename + alias removal) |
| `86a537a` | 3-4 | Weekly `af log review` systemd timer — units + idempotent installer (iter 1) |
| `d490c5f` | 3-3 | research/projects/education-and-showcases/ +5 entries: anthropics-courses, claude-agent-sdk-demos, anthropics/skills, wshobson/agents, florianbruniaux guide (iter 2) |
| `3f577e7` | 3-5 | Ratify plan-exec global node-id namespace + mark scope; new reference doc (iter 3) |

---

## 3. Remaining — ranked

Each entry has a size tag the SOP consumes. The `⭐ NEXT` marker points
at the current pick. Move it down as items finish.

### Session-surfaced follow-ups

- **⭐ NEXT  S-1** `[small]` Regenerate `docs/skill-tree.md` via `af tree --regenerate` — stale (omits `computer-control`, possibly others after A2 + renames).
- **S-2** `[medium]` New `af audit` CHECK 11 — validate `[modes.*]` manifest section the same way CHECK 1 validates `[skills.*]`.
- **S-3** `[medium]` `af check modes` — MODE.md frontmatter validator. Pending from behavioral-modes design plan.
- **S-4** `[small]` Upgrade `research` dispatcher description to full trigger-spec (currently brief prose; only dispatcher that hasn't been rewritten).
- **S-5** `[small]` Copy `feature-dev` slash command locally. NEXT_STEPS's original C2 assumption was wrong — `feature-dev` is a slash command, not a subagent. Would live under `commands/`.

### Tier 5 (small fixes)

- **5-1** `[small]` `af audit` CHECK 9 false positives on `command -v`-guarded binaries. Add a parse step that skips binaries inside `command -v <bin>` contexts.
- **5-2** `[trivial]` python-expert vs typescript-expert cosine similarity 0.42 per `af check distinct`. Benign template pairing; revisit only if routing confusion is observed. Tag `[needs-human]` unless routing data shows real confusion.
- **5-3** `[small]` `hooks/install-gemini-hooks.sh` parity — synced this session but drift will return. Add an audit check or a shared source-of-truth.
- **5-4** `[trivial]` `skill-logger.py` reads `tool_output`/`output` but canonical hook schema is `tool_response` (per N3 typed-payloads work). One-line fix.

### Tier 4 (design candidates — mostly `[speculative]`)

- **4-1** `[speculative]` Per-project modes — `af mode on --project` writes to `.claude/modes/` in the repo.
- **4-2** `[speculative]` Named mode bundles — `af mode preset research-deepdive` activates a curated set.
- **4-4** `[medium]` `af test-skill` automated pipeline — scaffolds workspace + dispatches subagent + renders report. Data-driven by existing `tests/<skill>/iteration-N/` layout.
- **4-5** `[speculative]` Per-skill `model:` frontmatter routing. Needs hook-time dispatch change. Defer until cost signal.
- **4-6** `[medium]` HTML eval-viewer for skill-tester. anthropics/skills ships one in skill-creator. We have raw data at `tests/<skill>/iteration-N/grades.json`.

### Monitoring (30-day)

- **M-1** `[needs-human]` Monitor 4 never-loaded leaves: `computer-control`, `dsa-expert`, `system-architecture-expert`, `agentfiles-manager`. If any stays zero-loads despite relevant tasks, re-open 1-1 for that skill.

---

## 4. Stop-run log

One entry per loop run that terminates. Appended by the stop protocol.

<!-- entries go here -->

---

## 5. Outside-repo (user must do manually)

These cannot be automated by the loop — they touch `~/.claude/` or
systemd state outside the repo.

- `systemctl --user enable --now dotoold` — activate input daemon for `computer-control`. Without it, `dotool` silently fails.
- `./hooks/install-hooks.sh` — re-sync `~/.claude/settings.json` to the new `modes.py`. The old `caveman-mode.py` is deleted; hook silently no-ops until the user re-installs.
- `rm ~/.claude/skills/skill-manager` — purge the stale alias symlink left over from the `agentfiles-manager` rename.
- `bash hooks/install-log-review-timer.sh` — install the weekly `af log review` systemd timer shipped in 3-4. Edit the `WorkingDirectory=` line first if the checkout isn't at `~/projects/agentfiles`.

---

## 6. Guard rails (persistent, session-agnostic)

- **Don't bulk-promote every draft under `docs/skills-drafts/`.** The human-in-the-loop gate exists because the heuristic surfaces session replays, not distilled skills. N24's rejection proved this.
- **Don't disable `af audit` checks.** Each one was added in response to real drift.
- **Don't convert skills to subagents proactively.** The 3-criteria rule (verbose-output + self-contained + tool-restriction) must all hold. 3 currently qualify (skill-tester, audit, security-review); that's probably it.
- **Don't add MCP servers / CLI tools preemptively.** The anti-bloat rule in `AGENTS.md` says capability, not surface area. Measure demand first.
- **Don't bulk-rewrite README files.** Users rely on current phrasing for search/muscle-memory; rewrites erase that context.

---

## 7. The one thing to remember

The improvement loop exists and the infrastructure is in place:

```
session → af log review → research/lessons/ → promote pattern → knowledge/K-NNN
                       ↘ anomalies.md → retrospective skill → skill edits
```

Before this session, nothing ran the crank. Item 3-4 finally wires it up.
After that lands, compound learning becomes automatic — no human needed
to remember to pull the handle.
