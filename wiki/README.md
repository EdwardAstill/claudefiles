# agentfiles wiki

The wiki is the system's long-term memory. Research findings, downloaded papers, and
lessons learned across sessions all live here. Agents should read the relevant pages
before making architectural decisions, and contribute back when they learn something
worth keeping. If it isn't written down, the next session will make the same mistake.

## Structure

- **`research/`** — deep-dive reference on harness design. Five foundational pages:
  - [`harness-foundations.md`](research/harness-foundations.md) — tool loop, context
    window, skills, subagents, verification gates. Comparative review of Claude Code,
    Aider, Cursor, Cline, OpenHands, Devin, Gemini CLI, Codex CLI.
  - [`context-engineering.md`](research/context-engineering.md) — tool-RAG, compaction,
    structured note-taking, handoff blocks, session resumption.
  - [`multi-agent-coordination.md`](research/multi-agent-coordination.md) — router,
    supervisor, orchestrator-workers, evaluator-optimizer; MAST failure taxonomy;
    DeepMind scaling study; ~15x token tax; when multi-agent helps vs hurts.
  - [`self-improving-agents.md`](research/self-improving-agents.md) — reflection,
    self-critique, skill accretion, feedback loops. Voyager, Reflexion, Self-Refine,
    Generative Agents, ChatDev.
  - [`memory-and-learning.md`](research/memory-and-learning.md) — episodic vs semantic
    vs procedural memory, retrieval strategies, observation→reflection→distillation
    loops. How a single-user personal system persists learning across sessions.
- **`papers/`** — downloaded PDFs plus an index of link-only references. Primary
  sources for everything in `research/`. See [`papers/README.md`](papers/README.md)
  for the full catalog.
- **`lessons-learned/`** — human-curated and agent-captured lessons from past
  sessions. One short markdown file per lesson; filename is a slug of the takeaway.
  See [`lessons-learned/README.md`](lessons-learned/README.md) for format.

## Conventions

- Every factual claim cites a source (a paper in `papers/`, a URL, or a specific
  session artifact).
- Cross-link liberally between pages — `research/` pages should reference the
  papers they draw from, and `lessons-learned/` should link to the research page
  that confirms or contradicts the lesson.
- When a page changes how the system should behave, also update `AGENTS.md` or the
  relevant `SKILL.md`. The wiki is reference; the skills and `AGENTS.md` are what
  agents actually read at runtime.

## How to add to the wiki

From inside a session:

- `af note "finding"` — captures short observations into `.agentfiles/notes.md`.
  Use this for anything that might be worth promoting later.
- Longer write-ups → `wiki/lessons-learned/<slug>.md`. Keep each lesson short:
  context, what happened, what to do differently next time, one or two citations.

For a new research topic:

- Run `af research <topic>` to scaffold a research prompt, feed the output back
  into the session, then write the synthesis into `wiki/research/<topic>.md`.
- Download supporting papers into `wiki/papers/` and link them from the research
  page.

## Relationship to existing reference docs

This wiki does not replace `docs/reference/`. In particular:

- [`docs/reference/agent-orchestration-patterns.md`](../docs/reference/agent-orchestration-patterns.md)
  is the short, opinionated synthesis. Research pages here **extend and deepen it**
  with full citations, implementation detail, and comparative tables.
- [`docs/reference/orchestration.md`](../docs/reference/orchestration.md) is the design
  spec for the current executor + manager architecture. Research pages cite it but
  never duplicate it.
- When a research page's evidence contradicts a current design choice, surface it in
  that page's "Implications for agentfiles" section rather than silently updating the
  spec. The spec change requires explicit review.

## Related

- [../README.md](../README.md) — project overview and mission.
- [../AGENTS.md](../AGENTS.md) — runtime guidance for agents working in this repo.
- [../docs/reference/agent-orchestration-patterns.md](../docs/reference/agent-orchestration-patterns.md)
  — routing and scaling research that this wiki builds on.
