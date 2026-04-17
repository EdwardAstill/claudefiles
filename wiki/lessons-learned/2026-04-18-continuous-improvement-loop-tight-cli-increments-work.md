# Continuous improvement loop — tight CLI increments work

## Context

The user ran `/loop 5m continue to expand and improve` during the growth-foundations
session. The loop kicked off a 5-minute recurring prompt with a 1-hour hard expiry,
giving Claude a bounded window of uninterrupted iteration on an open list of
system-improvement gaps (the "Implications for agentfiles" bullets captured earlier
in `2026-04-18-foundational-research-pass.md`).

## What happened

Each 5-minute tick landed one tight, self-contained improvement and committed it
before the next fire. By the end of the loop:

- `af archetype list/show/match` — turned the passive task-archetypes.json into an
  active routing helper (bag-of-words match over `signal_phrases`).
- `af check distinct` — Jaccard similarity scorer over skill descriptions; flags
  routing confusion before it happens.
- `af lessons new/list` — reduces capture friction to one command with a templated
  file.
- `af wiki list/grep/show` — makes the wiki directly consumable at the CLI.
- HANDOFF CONTEXT generalised in executor — not only on escalation, but on every
  subagent dispatch.
- Executor's Step 1 (Orient) now runs `af wiki list` so agents discover the wiki
  automatically.
- AGENTS.md now opens with a "Before planning, consult the wiki" block.

Each increment was 50–150 lines of code or doc, smoke-tested, and committed
independently. No increment depended on another being half-done.

## The lesson

**When Claude is given a bounded loop over a concrete gap list, the natural unit of
work is one CLI subcommand or one doc pointer per tick.** Bigger units starve the
loop (half-done work across ticks); smaller units are busywork. The 5-minute tick
aligns with "write + smoke-test + commit one tight thing".

The meta-lesson: **tools beat exhortation.** "Check the wiki before planning" in a
SKILL.md is weaker than `af wiki list` being in Step 1 of orient. Every capability
added as a CLI is now discoverable via `af --help` and composable; every capability
added only as prose in a SKILL.md is optional.

## Where this applies

- Any time the system has a list of specific, scoped gaps (not a vague "make it
  better"), prefer the `/loop Nm` pattern with a hard expiry over one long
  all-at-once push.
- When encoding new harness behaviour, ask: "is there a CLI that would make this
  behaviour the default path?" If yes, build the CLI before writing more prose.
- Pair each new CLI with a one-line pointer in `AGENTS.md` or the relevant SKILL.md.
  Without the pointer the tool is undiscoverable; without the tool the pointer is
  wishful.

## References

- Session branch: `feat/growth-wiki`
- Commits (reverse chronological): `36d0e30` orient wiring + this lesson,
  `533696d` wiki CLI, `f7b7a87` lessons CLI + HANDOFF generalisation,
  `acabbfe` check distinct, `af26956` archetype match, `45432ee` archetypes
  wired in SKILL.md, `8463acf` af research, `7cac7b7` archetypes registry,
  `28c7839` research wiki + papers, `381fcaf` mission + hub.
- Related research: `wiki/research/self-improving-agents.md` (skill accretion
  loop), `wiki/research/context-engineering.md` (tool-RAG distinguishability).
- Task archetypes: `docs/reference/task-archetypes.json`.
