# Foundational Research Pass — 2026-04-18

First real entry in `lessons-learned/`. Records what the initial `/manager`-driven
improvement session produced, what worked, and what should be picked up next.

## Context

The user asked for a broad foundation-building pass: a shortcut for launching deep
research, a Cappy-style wiki backed by downloaded studies, a task-archetypes registry
mapping big tasks to agent-group compositions, and a simple growth-oriented mission
statement in the README/AGENTS.md. They explicitly said "take initiative, don't ask
me anything".

## What was built

- `wiki/` — new top-level directory. Hub page, 5 research pages (harness-foundations,
  context-engineering, multi-agent-coordination, self-improving-agents,
  memory-and-learning), paper index, lessons-learned scaffold.
- `wiki/papers/` — 17 arxiv PDFs downloaded (RAG-MCP, MAST, DeepMind scaling,
  Reflexion, Voyager, Generative Agents, ReAct, Toolformer, Self-Refine, MemGPT,
  SWE-agent, ChatDev, MetaGPT, AutoGen, Prompt2DAG, agent-skills, agents-survey).
- `docs/reference/task-archetypes.{json,md}` — 15 archetypes mapped to agent groups,
  phases, parallel/sequential, risks.
- `tools/python/src/af/research.py` + wiring in `main.py` — `af research <topic>`
  scaffolds a prompt + output dir. Fish shortcut `afr` in dotfiles for
  one-keystroke launch.
- `README.md` + `AGENTS.md` mission blocks framing the system as a tool to fully
  enhance human capability, with continual self-improvement as the operating mode.

## What worked

- **Three parallel agents, non-overlapping file scopes.** Research wiki, CLI +
  archetypes, and growth-mission docs ran in background concurrently and produced
  clean deliverables without merge conflicts. Total wall clock ~10 minutes for
  the parallel phase.
- **Explicit file-scope constraints in each agent's prompt.** Every dispatch
  included a "do NOT touch these files" list so agents didn't clobber each
  other's work. This avoided the "bag of agents" overlap failure mode
  (see `wiki/research/multi-agent-coordination.md`).
- **The paper download side-effect.** Research agent dropped 17 PDFs into
  `wiki/papers/` while writing the research pages. The wiki now has primary
  sources on disk, not just URLs — future sessions can read them directly without
  re-fetching.

## What to pick up next

The research pages' **"Implications for agentfiles"** sections flagged concrete
gaps. Highest-leverage:

1. **Verification enforcement.** SWE-agent's ACI thesis shows verification is the
   single biggest harness lever. `verification-before-completion` is currently
   opt-in; it should become a Stop-hook so it always runs before a task is
   reported done. See `wiki/research/harness-foundations.md`.
2. **Context-fill monitoring.** No hook currently warns when context is filling.
   Anthropic's attention-budget work suggests a 70–80% threshold warning.
   See `wiki/research/context-engineering.md`.
3. **Retrospective → skill-edit proposals.** `af log review` produces
   `observations.md` but the loop stops there. The `retrospective` skill should
   emit concrete edit proposals for the skills that caused churn, not just flag
   them. See `wiki/research/self-improving-agents.md`.
4. **HANDOFF CONTEXT generalisation.** Currently only executor→manager uses the
   structured handoff block. Every subagent dispatch should, because context
   loss is the #1 MAS failure mode across every survey.
5. **`af check` distinctiveness scoring.** `af check` verifies REGION.md entries
   exist; it should also score skill-description distinctiveness (tool-RAG
   routing quality). Similar descriptions cause routing confusion.
6. **Task-archetypes integration.** The registry exists but nothing reads it
   yet. Next step is a hook into manager's planning phase and executor's
   routing decision — look up the user's phrasing against `signal_phrases` and
   surface the matching archetype.

## Small fixes

- README and AGENTS.md had drifting skill counts (61 at top, 48 in a subheading,
  68 actual). Dropped the counts entirely — `af agents --tree` is the live
  source of truth. Do this for any count that can drift.

## References

- Primary sources in `wiki/papers/`.
- Research synthesis: `wiki/research/*.md`.
- Session branch: `feat/growth-wiki` (commits `381fcaf`, `28c7839`, `7cac7b7`, `8463acf`).
