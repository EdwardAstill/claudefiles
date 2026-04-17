# Recent Improvements (2026-04-17)

Full critical pass on hooks, self-improvement loop, caveman system, docs alignment.

## Hooks — Now Fully Functional

**Problem:** SessionStart hook referenced nonexistent `task-analyser` skill → silent exit → users had to manually invoke every skill.

**Solution:** Fixed `hooks/session-start` to:
- Reference actual `using-agentfiles` skill
- 3-path fallback: plugin mode → user skills → ~/.claude/skills
- Injects skill content + pending routing anomalies on session start

**Plugin-mode hook mismatch:** `hooks/hooks.json` had only 3 hooks (SessionStart, Stop, Notifications), missing PostToolUse (skill-logger) and PreToolUse (safety-gate) that `install-hooks.sh` provided. Two installation paths → different behavior.

**Solution:** Unified both configs. All paths now register:
- PreToolUse: safety-gate.py (blocks dangerous bash patterns)
- PostToolUse: skill-logger.py (logs every tool call for analysis)
- UserPromptSubmit: caveman-mode.py (persistent mode re-injection)
- SessionStart: session-start (context + anomaly alerts)
- Stop/PermissionRequest/Notification: notify.py (desktop alerts + status)

## Self-Improvement Loop — Now Closes

**Problem:** skill-logger.py logs all tool calls, but session logs grow unbounded. `retrospective` skill exists but manual-only. No automatic detection of routing problems.

**Solution:**

1. **Log rotation** (skill-logger.py):
   - Session state files: 24h (old sessions cleaned up)
   - Session JSONL logs: 7 day retention (prevents 1.3MB creep)
   - agentfiles.jsonl: rolling 5 MB cap (discards oldest half when full)
   - Throttled to once/hour to avoid per-call overhead

2. **Anomaly detection** (notify.py):
   - On Stop event, scans this session's skill log
   - Flags: self-loops (skill calling itself), chain depth > 3, wasted loads (≥3× same skill)
   - Writes to ~/.claude/logs/anomalies.md for next session's context
   - Desktop notification with anomaly summary

3. **SessionStart surfacing** (hooks/session-start):
   - If anomalies.md exists + non-empty, session-start context includes flag + command to review
   - User sees "X session(s) had anomalies → run `af log anomalies`"

4. **New CLI command** (`af log anomalies [--clear]`):
   - Show all detected anomalies from recent sessions
   - `--clear` flag to delete after review

## Caveman Mode — Rebuilt from Scratch

**Old:** 6 levels (lite, full, ultra, wenyan-lite, wenyan-full, wenyan-ultra). Mode didn't persist past session start. No CLI control. Relied on AGENT.md which Claude Code doesn't read.

**New:** 3 levels only:

- **lite** — Drop filler (just/really/basically), pleasantries (sure/of course), hedging. Keep articles + grammar. No quality loss.
- **full** *(default)* — Drop articles too. Fragments OK. Short synonyms. ~60–70% token save, slight quality dip.
- **actual-caveman** — Grunt style with cave analogies. Novelty only.

**Persistence:** New UserPromptSubmit hook (caveman-mode.py) reads ~/.claude/caveman-mode every user turn and re-injects a short reminder. No mode drift over long conversations.

**CLI control:**
```bash
af caveman on full           # enable full (recommended)
af caveman on lite           # enable lite
af caveman on actual-caveman # enable cave-talk mode
af caveman off               # disable
af caveman                   # show current state
```

**CLAUDE.md:** Created ~/.claude/CLAUDE.md (previously missing) with caveman default + pointer to state file. Claude Code reads this on session start.

## Statusline — Now Part of Agentfiles

**Before:** `/home/eastill/dotfiles/.../statusline-command.sh` — separate maintenance burden, no caveman indicator.

**After:** `hooks/statusline.sh` in agentfiles repo:
- Shows: cwd, git branch, model, **[cv:<level>]** indicator (red, only when active), context %, 5h rate limit
- Automatically installed by `af install` → ~/.claude/settings.json.statusLine
- Symlink from ~/.claude/skills/hooks means updates propagate without re-run
- Fixed pre-existing `~` substitution bug (cwd not abbreviating correctly)

Dotfile copy removed (now redundant).

## Documentation — Aligned with Reality

**Skill count drift:** README said "40 skills", AGENTS.md said "39", docs/skill-tree.md listed 31, actual disk had 65 SKILL.md files. No single source of truth.

**Solutions:**

1. **Auto-generated skill tree:** New `tools/scripts/gen-skill-tree.py` generates docs/skill-tree.md from filesystem. Ran once to populate; can re-run anytime tree changes.

2. **Manifest sync:** Added 7 missing skills (dsa-expert, system-architecture-expert, documentation, documentation-maintainer, health-advisor, kb-critic, file-converter), removed stale make-quiz, fixed file-converter missing frontmatter. Disk and manifest now match exactly.

3. **Skill descriptions compressed:** Top 3 longest descriptions (ui, dsa, architecture) shortened to cut system-prompt bloat (~2 KB per session). Longer prose moved into skill body.

4. **Docs consolidated:** Merged docs/superpowers/plans → docs/plans, docs/superpowers/specs → docs/specs, removed empty docs/testing/, deleted duplicate docs/tools/external-tools.md. Single source of truth per topic.

## What Still Could Improve

- Caveman-lite, caveman-full as persistent CLAUDE.md defaults: currently off by default, user enables via `af caveman on`. Could default to `full` globally if desired.
- Per-turn caveman re-injection relies on UserPromptSubmit hook. If disabled, mode persists only for the current turn. Add a pre-session hook to freshen it? (Low priority.)
- Anomaly detection runs only on Stop, not during session. Could add a periodic check. (Low priority.)
- docs/ has 72 files across 10 dirs. Further consolidation possible (agent-performance, helpful-projects, reference overlap). Deferred.

## Testing

All new code tested:
- `hooks/session-start` produces valid JSON, injects using-agentfiles content + anomaly flags
- `hooks/caveman-mode.py` reads state file, emits correct UserPromptSubmit payloads for each level
- `af caveman` CLI: on/off/status/level commands functional
- `hooks/statusline.sh` shows caveman indicator, shortened cwd, git state, bars
- `af log anomalies` reads and displays anomalies from recent sessions
- Log rotation: marker throttle works, stale files pruned
- Manifest: no missing/stale entries after additions

Live state:
- Caveman mode: ON (full) — active at every user turn
- Hooks: 6 registered (SessionStart, PreToolUse, PostToolUse, UserPromptSubmit, Stop, PermissionRequest, Notification)
- Statusline: wired into ~/.claude/settings.json, shows [cv:full]
- Skills: 61 leaf skills on disk, 59 in manifest (routers not counted)
