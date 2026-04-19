# What belongs in agentfiles?

Rules for deciding whether something should live in this repo. Written after
the 2026-04-19 scope review.

This repo is **the agent system** — the skills, modes, hooks, subagents, and
CLI surface that make AI coding assistants (Claude Code, Gemini CLI) more
useful. Everything here earns its place by serving that mandate.

Standalone utilities (YouTube CLI, web scraper, screenshot tool, etc.) go
elsewhere, even if the agent system ends up using them. See [`EdwardAstill/eastill`](https://github.com/EdwardAstill/eastill) for the full repo index.

---

## The one question

> Does this thing reference — or enable — a skill, mode, hook, subagent, or
> agent concept?

**Yes** → it belongs here.
**No** → it goes in its own repo, and agentfiles might teach a skill about how
to use it.

---

## Tiers of what lives here

### Tier 1 — agent-system primitives (always)

The core product. Nothing else would make agentfiles agentfiles.

- `agentfiles/<category>/<skill>/SKILL.md` — skills
- `agentfiles/modes/<name>/MODE.md` — behavioral modes
- `agentfiles/agents/<name>.md` — subagent definitions (local copies of Claude
  Code built-ins, plus custom ones)
- `hooks/*.py`, `hooks/*.sh` — Claude Code / Gemini lifecycle hooks
- `agentfiles/includes/` — reusable skill fragments
- `commands/*.md` — slash commands

### Tier 2 — `af` CLI that drives the agent system

Any `af` subcommand whose job is to read, mutate, audit, or install pieces of
the agent system.

Included (stays):
- `af audit`, `af check`, `af context`, `af status`, `af versions`, `af tree`,
  `af routes`
- `af skill-find`, `af skill-usage`, `af test-skill`
- `af include`
- `af learn`, `af log`, `af metrics`
- `af mode` *(and the `af caveman` backwards-compat alias)*
- `af plan-exec`, `af plan-scaffold`
- `af archetype`
- `af ak` (agent knowledge)
- `af install`, `af setup`, `af tools`
- `af note`, `af read`, `af init`

### Tier 3 — reference docs and research

- `docs/reference/*.md` — how the system works
- `docs/plans/` — design plans (in-flight + archived)
- `docs/specs/` — design specs
- `docs/testing/` — skill-tester benchmark reports
- `docs/reports/` — periodic reviews
- `research/knowledge/` — curated K-NNN pages, referenced by `af ak`
- `research/projects/` — curated writeups on agent-ecosystem topics
- `research/lessons/` — session takeaways

### Tier 4 — intentionally NOT here (extract to own repos)

Standalone user-facing tools that are useful outside the agent system. These
get their own repo; agentfiles keeps a skill that teaches the agent to use
them.

| CLI | Extracts to | Skill that stays |
|---|---|---|
| `af youtube` | `EdwardAstill/yt-cli` | `youtube` skill |
| `af webscraper` | `EdwardAstill/webscraper` | `web-scraper` skill |
| `af terminal` | `EdwardAstill/termread` | `terminal-read` skill |
| `af screenshot` | `EdwardAstill/shotty` | folded into `computer-control` recipes |
| `af secrets` | `EdwardAstill/secrets` | — (no skill; ad-hoc use) |
| `af worktree` | `EdwardAstill/gwt` | `git-worktree-workflow` skill |

**Pattern:** the skill teaches *how to drive the tool*; the tool is a plain
CLI with no agent-specific behavior. Tools don't read the manifest, don't
import from `af.*`, don't care about skills.

Migration is a separate multi-session project — see `docs/plans/` when it
starts.

### Tier 5 — never belongs here

- Personal content (notes, journal, personal code). Goes in `EdwardAstill/knowledge` or a private repo.
- Generic utilities with no agent story (even small ones). They get their own
  repo even if tiny — future growth is easier than untangling.
- Tools that have their own external user community (foxpilot, readrun, etc.
  already live in their own repos — correct).

---

## Borderline cases — decided

### `af ak` stays

Queries curated `research/knowledge/` pages. The skill system reads these
directly. Keep. If the knowledge base ever grows general-purpose, revisit.

### `research/projects/` stays

Curated agent-ecosystem writeups. Not personal notes — referenced by the
learning loop and surfaced via `af ak`. Keep.

### `af install` / `af setup` stay

These wire the agent system into `~/.claude/` and `~/.gemini/`. Without them,
nothing in this repo reaches the runtime. Definitive tier-2.

### Subagent definitions (`agentfiles/agents/`) stay

Stays. Tier-1. Seven are verbatim copies of Claude Code built-ins (tracked in
git so the agent system doesn't drift when Claude Code ships updates).

### `commands/feature-dev.md` stays

Slash commands are agent-adjacent. Tier-1. Currently not wired by `af install`
(see backlog item S-8); when wired, the `commands/` dir is a first-class
install target.

---

## Adding new things — a checklist

Before creating a new skill, mode, hook, or `af` subcommand, ask:

1. **Does it serve the agent system?** (see the one question above)
   - Yes → proceed.
   - No → make a new repo; add it to [`eastill`](https://github.com/EdwardAstill/eastill).

2. **If it's a new `af` subcommand:** does the work it does require reading
   manifest / skills / modes / agent state?
   - Yes → tier-2, belongs here.
   - No → extract as standalone CLI.

3. **If it's a new skill:** does it reference an external tool?
   - Yes → the skill describes how to use the tool; the tool lives elsewhere.
   - No → fully lives here.

4. **If you're unsure:** flag it in `NEXT_STEPS.md` §3 with tag
   `[needs-scoping]` and come back with a thought-through proposal.

---

## Health checks

- `af audit` enforces manifest parity (11 checks).
- `af check plans` / `af check modes` catch drift between plans/modes and
  their implementations.
- The test suite (`pytest tools/python/tests/`) guards the `af` CLI
  invariants.
- This doc is the structural layer above all of that — review it when scope
  pressure appears.

---

## Rule of thumb

If you're tempted to add a `af <thing>` subcommand and can explain what it
does without mentioning skills / modes / hooks / agents / manifest, you're
looking at a standalone tool. Extract it.

If removing the subcommand would make the agent system worse at its job,
it belongs here.
